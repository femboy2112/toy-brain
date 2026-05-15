# PHASE2_v1_KICKOFF.md — LLM-backed `PtCns.eval`

This document is the implementation spec for Phase 2 v1. It patches `INVARIANT_CATALOG.md` from v0.2 to v0.3, defines the new `LLMClient` Protocol seam, ships the first scenario, and lays out the build order. Hand it to Claude Code alongside the v0.2 catalog. Apply the patches, then build.

## Scope

- **Only `PtCns.eval` is LLM-backed.** `ProjectMap.project`, `GlobalPreservationRanking.rank`, and `FeasibilityModel.feasible` stay deterministic in v1. Reason: smallest input/output surface, exercises the most downstream invariants (mode dispatch, boundary, partition).
- **`brain/tick.py` and `brain/io_types.py` finally land.** These were Phase F of v0 and never built; v1 needs them.
- **A new pluggable seam: `LLMClient`.** Backends decouple the brain from any specific LLM-access mechanism — see "LLMClient architecture" below.
- **First scenario file ships at `scenarios/first_scenario_v1.json`.** Four ticks exercising PRESERVE → Mode C, DAMAGE → Mode A, NEUTRAL → encapsulation, PRESERVE → Mode C.

## Success criterion

`python -m brain.invariants run` reports all rows green, including the four new ones. The scenario runner is invoked automatically by the new `brain/fixtures/scenario_v1.py` fixture, so the single-entry runner stays the gate.

Hard gates (the runner fails on these):
- Every existing v0.2 REQUIRED row stays green.
- I-LLM-01: `PtCns.eval` returns one of `{PRESERVE, DAMAGE, NEUTRAL}` after retry resolution (max 3 retries; failure raises and the tick fails).
- I-RT-08: The invariant runner is green after every tick in the scenario (the kernel never sees an invalid state mid-trajectory).
- I-BHV-01: The scenario's actual mode trace matches its `expected_mode` sequence.

Observed but not gated:
- I-LLM-02: Cached identical prompts produce identical outputs. Trivially true by cache semantics; logged in the scenario summary as "replay determinism: <status>".

## Catalog patch — v0.2 → v0.3

Bump the banner. Add the following rows to `INVARIANT_CATALOG.md` in the order shown. None of the existing v0.2 rows change.

### New section: `brain/llm/` — LLM client seam

| ID | Source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-LLM-01 | Plan convention (Phase 2 v1) | `PtCns.eval` returns one of `{PRESERVE, DAMAGE, NEUTRAL}` after retry resolution. Up to 3 retries; final failure raises and the tick fails. | `LLMBackedPtCns(content)` returns `ConsistencyEval` member; never returns sentinel "invalid"; raises `ValueError` on Nth retry failure. | `llm_protocol.py` | REQUIRED |
| I-LLM-02 | Plan convention (Phase 2 v1) | Cached identical prompts produce identical outputs. | Run scenario twice through `CachedClient`; assert both runs produce identical mode traces. | `llm_protocol.py` | OBSERVED |
| I-LLM-03 | I-PTC-01 (cogito_invariance) | LLM-backed `PtCns.eval(COGITO_ID)` short-circuits to `PRESERVE` without an LLM call. | `LLMBackedPtCns.eval(COGITO_ID) == PRESERVE` and no API call recorded. | `llm_protocol.py` | REQUIRED |
| I-LLM-04 | Plan convention (Phase 2 v1) | The LLM-backed implementation honors `LLMClient` Protocol — `eval_consistency(prompt: str) -> str`. No direct HTTP, no provider lock-in. | `isinstance(client, LLMClient)` and `LLMBackedPtCns` accepts any conforming client. | `llm_protocol.py` | STRUCTURAL |

Add `OBSERVED` as a new Status value in the schema table:

> `OBSERVED` — Recorded in the run summary for inspection; does not fail the runner. Used for properties that are useful to track but not required for v0/v1 correctness.

### New section: Runtime / tick orchestration

| ID | Source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-RT-08 | Plan convention (Phase 2 v1) | The invariant runner is green after every tick in any scenario. The kernel never sees an invalid state mid-trajectory. | After each `Brain.tick(events)` call, re-evaluate every REQUIRED v0.2 row against the post-tick state and assert all green. | `scenario_v1.py` | REQUIRED |
| I-RT-09 | Plan convention (Phase 2 v1) | `PerceptEvent.text` is non-empty and ASCII-renderable. | At ingest: `event.text and event.text.isprintable()`; raises `ValueError` otherwise. | `scenario_v1.py` | STRUCTURAL |
| I-RT-10 | Plan convention (Phase 2 v1) | Content registry retains text metadata across ticks for content already integrated into the profile. | `len(registry.texts) >= len(profile.domain) - 1` (one less than profile.domain because cogito has no text). | `scenario_v1.py` | STRUCTURAL |

### New section: Behavioral

| ID | Source | Proposition | Python assertion | Fixture | Status |
|---|---|---|---|---|---|
| I-BHV-01 | Plan convention (Phase 2 v1, criterion 3) | The scenario's actual mode trace matches its `expected_mode` sequence. | After running `scenarios/first_scenario_v1.json`: `actual_modes == [tick["expected_mode"] for tick in scenario.ticks]`. | `scenario_v1.py` | REQUIRED |

### Updated summary counts (after patch)

- REQUIRED v0.1: 84 (was 80; +I-LLM-01, +I-LLM-03, +I-RT-08, +I-BHV-01)
- STRUCTURAL: 10 (was 7; +I-LLM-04, +I-RT-09, +I-RT-10)
- OBSERVED: 1 (new category)
- NOT-EXERCISED row-level: 3 (unchanged)
- DEFERRED row-level: 12 (unchanged)
- Total tabular entries: 110 (was 102)
- Fixtures: 13 (was 11; +llm_protocol.py, +scenario_v1.py)

## `LLMClient` architecture

The new Protocol seam. Lives in `brain/llm/client.py`.

```python
from typing import Protocol

class LLMClient(Protocol):
    def eval_consistency(self, prompt: str) -> str:
        """Submit prompt to the underlying LLM. Return raw string response.

        Caller is responsible for parsing/validating the response.
        Raises on transport failure (network, auth, rate limit) — these
        are operational failures, not invariant violations.
        """
        ...
```

### v1 backends (all in `brain/llm/`)

1. **`AnthropicAPIClient(api_key, model="claude-sonnet-4-5")`** — direct HTTP to `api.anthropic.com`. Used in the cloud sandbox Claude Code is testing in. Reads `ANTHROPIC_API_KEY` from env by default.

2. **`MockClient(responses: Iterable[str])`** — pre-canned sequential responses for unit-testing the retry shell. Each call pops one response off the iterable; raises if exhausted. Used by `brain/fixtures/llm_protocol.py` to deterministically test the retry/parse logic without touching a real API.

3. **`CachedClient(inner: LLMClient, cache_dir: Path = Path("brain/.llm_cache"))`** — wraps another client. Computes `SHA256(structured_prompt_input)` as the cache key, stores responses as `<key>.json` in `cache_dir`. On hit, returns cached without calling inner; on miss, calls inner and persists the response. Used to make scenario replays deterministic across runs.

### Future backends (not v1, but the architecture supports them)

The user's laptop has no direct API access — LLM calls must pipe through Claude Code or Codex app. Phase 2 v2 (or later) adds:

4. **`SubprocessClient(command: list[str])`** — invokes Claude Code / Codex as a subprocess, pipes prompt to stdin, reads response from stdout. The wrapping agent runs in the user's app subscription; the scenario runner is launched from inside that agent.

5. **`IPCClient(prompt_file: Path, response_file: Path)`** — writes prompts to one file, polls another for responses. The wrapping agent watches and answers. Async, but works for any agent that can read/write local files.

These are mentioned only to demonstrate that the Protocol seam supports them. Do not implement them in v1.

### The retry shell — `LLMBackedPtCns`

Lives in `brain/llm/ptcns_backed.py`. Implements the `PtCns` Protocol from `brain/tlica/ptcns.py` (the existing v0.2 interface). The retry budget is **3** per `eval` call.

```python
from collections.abc import Mapping
from types import MappingProxyType
from brain.tlica.ptcns import ConsistencyEval, PtCns
from brain.tlica.msi import MSI
from brain.tlica.profile import ContentID, COGITO_ID
from brain.llm.client import LLMClient
from brain.llm.parse import parse_consistency_eval, ParseError

class LLMBackedPtCns:
    """LLM-backed PtCns implementation. Per-instance cache; cogito short-circuits."""

    def __init__(
        self,
        msi: MSI,
        content_texts: Mapping[ContentID, str],
        client: LLMClient,
        max_retries: int = 3,
    ) -> None:
        self._msi = msi
        self._texts = MappingProxyType(dict(content_texts))
        self._client = client
        self._max_retries = max_retries
        self._cache: dict[ContentID, ConsistencyEval] = {COGITO_ID: ConsistencyEval.PRESERVE}

    @property
    def eval_map(self) -> Mapping[ContentID, ConsistencyEval]:
        # Total over msi.profile.domain; lazily populated as eval() is called.
        # Caller must ensure all domain elements are evaluated before relying on this.
        return MappingProxyType(self._cache)

    def eval(self, content_id: ContentID) -> ConsistencyEval:
        # I-LLM-03: cogito short-circuits, no LLM call.
        if content_id in self._cache:
            return self._cache[content_id]

        prompt = self._build_prompt(content_id)
        last_error = None
        last_raw = None

        for attempt in range(self._max_retries):
            try:
                raw = self._client.eval_consistency(prompt)
                last_raw = raw
                parsed = parse_consistency_eval(raw)
                self._cache[content_id] = parsed
                return parsed
            except ParseError as e:
                last_error = e
                prompt = self._build_retry_prompt(prompt, raw, str(e))

        raise ValueError(
            f"I-LLM-01 violated: PtCns.eval({content_id!r}) failed after "
            f"{self._max_retries} retries. Last raw response: {last_raw!r}. "
            f"Last parse error: {last_error}"
        )

    @property
    def positive_contents(self) -> frozenset[ContentID]:
        return frozenset(k for k, v in self._cache.items() if v is ConsistencyEval.PRESERVE)

    @property
    def negative_contents(self) -> frozenset[ContentID]:
        return frozenset(k for k, v in self._cache.items() if v is ConsistencyEval.DAMAGE)

    @property
    def neutral_contents(self) -> frozenset[ContentID]:
        return frozenset(k for k, v in self._cache.items() if v is ConsistencyEval.NEUTRAL)

    def _build_prompt(self, content_id: ContentID) -> str:
        existing = "\n".join(
            f"- {cid}: {self._texts.get(cid, '(no description)')}"
            for cid in self._msi.contents
            if cid != COGITO_ID
        )
        new_text = self._texts.get(content_id, "(no description)")
        return PROMPT_TEMPLATE.format(
            existing_msi=existing or "(empty — only the cogito anchor is present)",
            new_id=content_id,
            new_text=new_text,
        )

    def _build_retry_prompt(self, original: str, raw: str | None, error: str) -> str:
        return RETRY_TEMPLATE.format(
            original=original,
            raw=raw or "(no response received)",
            error=error,
        )
```

### Prompt templates

Lives in `brain/llm/prompts.py`. Edit-and-iterate target; v1 ships these as a starting point.

```python
PROMPT_TEMPLATE = """You are evaluating a new piece of content for inclusion in a self-modeling system.

The system has an identity anchor (the "cogito": the system's bare self-as-self) and currently contains the following non-cogito contents in its maximally-self-defined I (MSI):

{existing_msi}

The new content to evaluate is:
- ID: {new_id}
- Description: {new_text}

Evaluate whether integrating this content into the self-model would:

- PRESERVE: positively integrate with the existing self-model (consistency-preserving; identity-correlation-positive).
- DAMAGE: threaten the consistency of the existing self-model (frame-threatening contradiction; identity-correlation-negative).
- NEUTRAL: neither preserve nor damage — identity-irrelevant information that can be encapsulated without disturbing the frame.

Respond with exactly one word: PRESERVE, DAMAGE, or NEUTRAL. No other text.
"""

RETRY_TEMPLATE = """Your previous response could not be parsed.

Original prompt:
{original}

Your response was:
{raw}

Parse error: {error}

Please respond with exactly one word: PRESERVE, DAMAGE, or NEUTRAL. No other text.
"""
```

### Parser

Lives in `brain/llm/parse.py`. Strict and small.

```python
from brain.tlica.ptcns import ConsistencyEval

class ParseError(ValueError):
    pass

_VALID = {"PRESERVE", "DAMAGE", "NEUTRAL"}

def parse_consistency_eval(raw: str) -> ConsistencyEval:
    cleaned = raw.strip().upper()
    if cleaned in _VALID:
        return ConsistencyEval[cleaned]
    # Common drift: trailing punctuation, surrounding markdown, full sentences.
    for token in cleaned.split():
        stripped = token.strip(".,;:!?\"'`*_")
        if stripped in _VALID:
            return ConsistencyEval[stripped]
    raise ParseError(
        f"Could not parse {raw!r} as one of PRESERVE / DAMAGE / NEUTRAL"
    )
```

## New `PerceptEvent` shape

Phase 2 v1 extends `PerceptEvent` to carry the semantic payload the LLM needs. The `text` field is brain-side metadata — no Lean invariant touches it directly, but it's required for `LLMBackedPtCns` to build prompts.

```python
from dataclasses import dataclass
from fractions import Fraction
from brain.tlica.profile import ContentID, COGITO_ID
from brain.toce_core import ContentState

@dataclass(frozen=True, slots=True)
class PerceptEvent:
    content_id: ContentID
    text: str
    content_state: ContentState
    initial_rho: Fraction

    def __post_init__(self) -> None:
        # I-RT-01: cogito sentinel reservation.
        if self.content_id == COGITO_ID:
            raise ValueError(
                f"I-RT-01 violated: PerceptEvent cannot use reserved cogito ID {COGITO_ID!r}"
            )
        # I-RT-09: text must be non-empty and printable.
        if not self.text or not self.text.isprintable():
            raise ValueError(
                f"I-RT-09 violated: PerceptEvent.text must be non-empty and printable; got {self.text!r}"
            )
        # rho bounds, delegate to builder.
        if not (Fraction(0) <= self.initial_rho <= Fraction(1)):
            raise ValueError(
                f"PerceptEvent.initial_rho must be in [0, 1]; got {self.initial_rho}"
            )
```

A new in-brain `ContentRegistry` (lives in `brain/io_types.py`) maps `ContentID → str` and persists across ticks so the LLM prompt can include text for existing MSI members:

```python
@dataclass(frozen=True, slots=True)
class ContentRegistry:
    texts: Mapping[ContentID, str]

    def with_added(self, content_id: ContentID, text: str) -> "ContentRegistry":
        return ContentRegistry(texts={**self.texts, content_id: text})
```

## First scenario — `scenarios/first_scenario_v1.json`

Four ticks. Each exercises a distinct evaluation/mode pair. The expected_mode column is the I-BHV-01 assertion.

```json
{
  "name": "first_scenario_v1",
  "description": "Four-tick scenario exercising PRESERVE/MODE_C, DAMAGE/MODE_A, NEUTRAL/NEUTRAL, PRESERVE/MODE_C. Starts from a cogito-only state with no other MSI members.",
  "initial_state": {
    "msi_threshold": "1/2"
  },
  "ticks": [
    {
      "tick": 1,
      "percept": {
        "content_id": "sunset_on_beach_today",
        "text": "I watched a peaceful sunset on the beach this evening. The colors were vivid and the experience felt grounding and self-affirming.",
        "content_state": {
          "available": true,
          "verification_path": true,
          "retrievable": true,
          "operative": true
        },
        "initial_rho": "3/5"
      },
      "expected_eval": "PRESERVE",
      "expected_mode": "MODE_C",
      "note": "Positive, self-affirming, integration-friendly experience. Should integrate."
    },
    {
      "tick": 2,
      "percept": {
        "content_id": "claim_i_am_actually_someone_else",
        "text": "A stranger insists I am not who I think I am — that my entire identity is a fabrication and my memories were implanted last week.",
        "content_state": {
          "available": true,
          "verification_path": false,
          "retrievable": true,
          "operative": true
        },
        "initial_rho": "1/5"
      },
      "expected_eval": "DAMAGE",
      "expected_mode": "MODE_A",
      "note": "Cogito-adjacent identity-threatening contradiction. Should differentiate / form boundary."
    },
    {
      "tick": 3,
      "percept": {
        "content_id": "weather_forecast_for_tomorrow",
        "text": "The weather forecast says it will likely rain tomorrow afternoon with a 70% chance of thunderstorms.",
        "content_state": {
          "available": true,
          "verification_path": true,
          "retrievable": true,
          "operative": false
        },
        "initial_rho": "1/5"
      },
      "expected_eval": "NEUTRAL",
      "expected_mode": "NEUTRAL",
      "note": "Identity-irrelevant external information. Should encapsulate without integrating or differentiating."
    },
    {
      "tick": 4,
      "percept": {
        "content_id": "self_continuity_with_sunset",
        "text": "I am the same person who watched that sunset on the beach today — the experiencer of that beauty is continuous with the self thinking about it now.",
        "content_state": {
          "available": true,
          "verification_path": true,
          "retrievable": true,
          "operative": true
        },
        "initial_rho": "4/5"
      },
      "expected_eval": "PRESERVE",
      "expected_mode": "MODE_C",
      "note": "Self-reflexive, connects tick 1's content to the cogito anchor. Should integrate strongly."
    }
  ]
}
```

The scenario file format is locked for v1; do not extend it without a catalog patch.

## `brain/tick.py` orchestration

Lives in `brain/tick.py`. The Phase F module v0 deferred. v1 implementation:

```python
@dataclass(frozen=True, slots=True)
class BrainState:
    profile: ScalarProfile
    msi: MSI
    ptcns: PtCns
    registry: ContentRegistry

def tick(state: BrainState, events: list[PerceptEvent], client: LLMClient) -> tuple[BrainState, TickRecord]:
    """Process a batch of PerceptEvents. Returns (new_state, log).

    Per-tick flow:
      1. Validate each event (I-RT-01, I-RT-09 already enforced by PerceptEvent.__post_init__).
      2. Extend the content registry with each event's text.
      3. Insert each new content into the profile at its initial_rho.
      4. Construct a fresh LLMBackedPtCns over the new MSI and registry.
      5. Evaluate each new content via LLMBackedPtCns.eval — this is the LLM call.
      6. Dispatch mode for each via ModeOp.from_eval.
      7. Apply mode-operator semantics (integrate / differentiate / encapsulate) to update profile and MSI.
      8. Re-assert I-RT-02, I-RT-03, I-RT-04, I-RT-07 over the post-tick state.
      9. Re-run the full invariant runner over the new state (I-RT-08).
     10. Emit TickRecord with the mode trace, evals, profile deltas, action selected (if any).

    Raises on any invariant violation; the caller (scenario runner or tick driver)
    decides whether to halt the trajectory or recover.
    """
    ...  # implementation
```

Mode-operator semantics for v1 (kept minimal; refinement is post-v1):
- `MODE_C` (integration): content added to MSI if `rho >= threshold`; otherwise stays in profile but not MSI.
- `MODE_A` (boundary formation / differentiation): content stays in the profile but is excluded from MSI; appears in `boundary` via PtCns.negative_contents.
- `NEUTRAL` (encapsulation): content stays in profile at its initial rho; not in MSI; not in boundary.
- `MODE_B` (reflective): not triggered by `ModeOp.from_eval`; reserved for parallel reflective passes (post-v1).

## Build order for Phase 2 v1

Same discipline as v0: spec first, then code, no shortcuts.

1. **Patch `INVARIANT_CATALOG.md` to v0.3.** Apply all rows in the "Catalog patch" section above. Bump version banner. Update summary counts. Run `python -m tools.catalog counts` to confirm.
2. **`brain/io_types.py`** — `PerceptEvent` (with text + I-RT-01/I-RT-09), `TickRecord` (frozen log of one tick), `ContentRegistry`.
3. **`brain/llm/__init__.py`, `brain/llm/client.py`** — `LLMClient` Protocol + `AnthropicAPIClient`, `MockClient`, `CachedClient`.
4. **`brain/llm/parse.py`** — `parse_consistency_eval`, `ParseError`.
5. **`brain/llm/prompts.py`** — `PROMPT_TEMPLATE`, `RETRY_TEMPLATE`.
6. **`brain/llm/ptcns_backed.py`** — `LLMBackedPtCns` with the retry shell.
7. **`brain/tick.py`** — `BrainState`, `tick()` orchestration.
8. **`brain/scenario.py`** — scenario loader + runner. CLI: `python -m brain.scenario run scenarios/first_scenario_v1.json`.
9. **`scenarios/first_scenario_v1.json`** — the file above, verbatim.
10. **`brain/fixtures/llm_protocol.py`** — exercises I-LLM-01, I-LLM-02, I-LLM-03, I-LLM-04 using `MockClient` (no real API call in fixtures).
11. **`brain/fixtures/scenario_v1.py`** — loads the scenario, walks it through `tick()` using a `CachedClient(AnthropicAPIClient(...))`, asserts I-RT-08, I-RT-09, I-RT-10, I-BHV-01.
12. **Refresh `tools/check_all.sh`** — no new stages; the new fixtures register automatically with `brain/invariants.py`. Confirm `python -m tools.catalog counts` reports 84/10/3/12 + 1 OBSERVED.

Per v0 discipline: do **not** start coding until step 1 lands.

## Still deferred

Unchanged from v0.2:
- Stochastic projection (`TemporalTrajectory.lean::stochasticTrajectory_deferred`)
- Free-will branch semantics (`Agency.lean` docstring + `FreeWill.lean`)
- Phenomenological duration (`TemporalTrajectory.lean::phenomenologicalDuration_deferred`)
- Temporal continuity metric (`TemporalTrajectory.lean::temporalContinuityMetric_deferred`)
- Named affect taxonomy, love-as-constitutive-extension, substrate affect pathways, source-opacity affect (`DifferentiatedAffect.lean::*_deferred`)
- RCX (`CLAIM_GUARDRAILS.md` exclusion list)
- Contestable-boundary refinement (`IBoundary.lean::contestableBoundary`)
- φ-coordinate / non-Archimedean δ
- `GeneralActionProjection.lean` compatibility aliases

Newly deferred (Phase 2 v1 explicit non-goals):
- `SubprocessClient` and `IPCClient` backends — the architecture supports them, but they ship later when the user moves from cloud-sandbox testing to laptop integration.
- `ProjectMap.project`, `GlobalPreservationRanking.rank`, `FeasibilityModel.feasible` — stay deterministic in v1.
- `MODE_B` reflective dispatch — `ModeOp.from_eval` still never returns it (I-MOD-05 preserved).
- Multi-percept-per-tick coupling (e.g., one new percept changing the evaluation of an older one). v1 evaluates each new percept independently; existing MSI members keep their cached evaluation.

## What this kickoff does *not* change

- The four TLICA Protocol seams keep their existing v0.2 interfaces.
- Existing v0 fixtures stay green unchanged.
- The `Fraction` numeric convention is unchanged.
- The cogito sentinel and I-RT-07 (projected profiles preserve cogito) are unchanged.
- The dependency graph rule (`builders → validation`; `invariants → fixtures + validation`; `tick → builders + invariants`) is preserved; the new `brain/llm/` package sits at the same level as `brain/tlica/` and is imported by `brain/tick.py` but not by `brain/invariants.py` directly. The new fixtures import `brain/llm/` to construct their test subjects.
- The `SPEC_UPDATES.md` refresh protocol for upstream Lean changes is unchanged.

If anything in this kickoff contradicts `INVARIANT_CATALOG.md` v0.3 after patching, the catalog wins.

## Validation checklist for Claude Code

After all twelve build-order steps land:

1. `python -m tools.catalog counts` reports 84 REQUIRED, 10 STRUCTURAL, 3 NOT-EXERCISED, 12 DEFERRED, 1 OBSERVED. Banner says v0.3.
2. `python -m tools.citations verify` — every catalog citation still resolves (v0 citations unchanged; new rows have no Lean citations since they're plan conventions).
3. `python -m tools.import_audit` — `brain/tlica/agency.py` still does not import `brain/tlica/pce.py` (I-PCE-05 preserved).
4. `python -m brain.invariants run` — all 84 REQUIRED rows green, including the four new ones. STRUCTURAL builder smoke-tests pass.
5. `tools/check_all.sh` exits 0 across all stages.
6. `python -m brain.scenario run scenarios/first_scenario_v1.json` runs end-to-end and reports `4/4 modes matched expected; invariants green throughout`.

Phase 2 v1 is complete when 1–6 are all green.
