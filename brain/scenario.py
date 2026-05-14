"""Scenario loader + runner (Phase 2 v1).

Loads ``scenarios/<name>.json``, walks each tick through
``brain.tick.tick(...)``, records the eval/mode trace, and reports
whether the actual modes matched the scenario's ``expected_mode``
sequence.

CLI:
    python -m brain.scenario run <path/to/scenario.json>

Default client = ``CachedClient(AnthropicAPIClient())``. The fixture
path uses a ``MockClient`` seeded from ``expected_eval`` for
deterministic runner output.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from brain.io_types import PerceptEvent, TickRecord
from brain.llm.client import (
    AnthropicAPIClient,
    CachedClient,
    ClaudeCLIClient,
    LLMClient,
)
from brain.tick import BrainState, initial_state, tick
from brain.tlica.modes import ModeOp
from brain.tlica.profile import ContentID
from brain.tlica.ptcns import ConsistencyEval
from brain.toce_core import ContentState
from brain.trace import CognitionTracer, FileTracer, NullTracer, make_tracer_from_env

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class ScenarioTick:
    tick: int
    percept: PerceptEvent
    expected_eval: ConsistencyEval
    expected_mode: ModeOp
    note: str = ""


@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    name: str
    description: str
    initial_msi_threshold: Fraction
    ticks: tuple[ScenarioTick, ...]


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    spec: ScenarioSpec
    actual_evals: tuple[ConsistencyEval, ...]
    actual_modes: tuple[ModeOp, ...]
    final_state: BrainState
    records: tuple[TickRecord, ...]

    @property
    def all_modes_matched(self) -> bool:
        return self.actual_modes == tuple(t.expected_mode for t in self.spec.ticks)


def _parse_content_state(payload: dict) -> ContentState:
    return ContentState(
        available=bool(payload["available"]),
        verification_path=bool(payload["verification_path"]),
        retrievable=bool(payload["retrievable"]),
        operative=bool(payload["operative"]),
    )


def _parse_percept(payload: dict) -> PerceptEvent:
    return PerceptEvent(
        content_id=ContentID(payload["content_id"]),
        text=payload["text"],
        content_state=_parse_content_state(payload["content_state"]),
        initial_rho=Fraction(payload["initial_rho"]),
    )


def load_scenario(path: Path) -> ScenarioSpec:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    ticks = tuple(
        ScenarioTick(
            tick=int(t["tick"]),
            percept=_parse_percept(t["percept"]),
            expected_eval=ConsistencyEval[t["expected_eval"]],
            expected_mode=ModeOp[t["expected_mode"]],
            note=t.get("note", ""),
        )
        for t in raw["ticks"]
    )
    return ScenarioSpec(
        name=raw["name"],
        description=raw.get("description", ""),
        initial_msi_threshold=Fraction(raw["initial_state"]["msi_threshold"]),
        ticks=ticks,
    )


def run_scenario(
    spec: ScenarioSpec,
    client: LLMClient,
    tracer: CognitionTracer | None = None,
) -> ScenarioResult:
    """Walk every tick of ``spec`` through ``brain.tick.tick`` with ``client``.

    Phase 2 v1.1: ``tracer`` defaults to ``make_tracer_from_env()`` (file
    tracer if ``BRAIN_TRACE_PATH`` is set, otherwise null). The same
    tracer is passed into ``tick()`` per scenario tick and ``close()``
    is called in a ``finally`` so JSONL streams flush even if a tick
    raises.
    """
    tracer = tracer if tracer is not None else make_tracer_from_env()
    state = initial_state(msi_threshold=spec.initial_msi_threshold)
    actual_evals: list[ConsistencyEval] = []
    actual_modes: list[ModeOp] = []
    records: list[TickRecord] = []
    try:
        for idx, scenario_tick in enumerate(spec.ticks):
            state, record = tick(
                state,
                [scenario_tick.percept],
                client,
                tracer=tracer,
                tick_id=idx + 1,
            )
            # P2: tick() propagates tick_id to TickRecord.tick_index
            # directly; no override needed (scenario was previously
            # stamping 0-based, which was brittle).
            records.append(record)
            actual_evals.append(record.eval_map[scenario_tick.percept.content_id])
            if record.triggered_mode is None:
                raise RuntimeError(
                    f"scenario tick {scenario_tick.tick}: triggered_mode is None"
                )
            actual_modes.append(record.triggered_mode)
        return ScenarioResult(
            spec=spec,
            actual_evals=tuple(actual_evals),
            actual_modes=tuple(actual_modes),
            final_state=state,
            records=tuple(records),
        )
    finally:
        tracer.close()


def _cmd_run(args: argparse.Namespace) -> int:
    spec = load_scenario(Path(args.path))
    # Tracer precedence (per kickoff toggle table):
    #   --trace FLAG   > BRAIN_TRACE_PATH env > NullTracer().
    if args.trace:
        tracer: CognitionTracer = FileTracer(Path(args.trace))
    else:
        tracer = make_tracer_from_env()
    # Share the tracer with the cached LLM stack so cache_hit /
    # cache_miss events thread through the same JSONL.
    inner: LLMClient
    if args.client == "claude-cli":
        inner = ClaudeCLIClient(tracer=tracer)
    else:
        inner = AnthropicAPIClient(tracer=tracer)
    client: LLMClient = CachedClient(inner, tracer=tracer)
    result = run_scenario(spec, client, tracer=tracer)

    matched = sum(
        1 for a, t in zip(result.actual_modes, spec.ticks) if a is t.expected_mode
    )
    total = len(spec.ticks)
    print(f"\nScenario: {spec.name}")
    for idx, t in enumerate(spec.ticks):
        ok = "ok" if result.actual_modes[idx] is t.expected_mode else "!!"
        print(
            f"  tick {t.tick}: eval={result.actual_evals[idx].name:8s} "
            f"mode={result.actual_modes[idx].name:7s} "
            f"(expected eval={t.expected_eval.name}, mode={t.expected_mode.name})  {ok}"
        )
    status = (
        "invariants green throughout"
        if result.all_modes_matched
        else "MODE TRACE MISMATCH"
    )
    print(f"\n{matched}/{total} modes matched expected; {status}")
    return 0 if result.all_modes_matched else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="brain.scenario")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run", help="Run a scenario JSON file end-to-end.")
    p_run.add_argument("path")
    p_run.add_argument(
        "--trace",
        metavar="PATH",
        help="Write a JSONL cognition trace to PATH. Overrides BRAIN_TRACE_PATH env var.",
    )
    p_run.add_argument(
        "--client",
        choices=("anthropic-api", "claude-cli"),
        default="anthropic-api",
        help=(
            "LLM backend. 'anthropic-api' uses AnthropicAPIClient (requires "
            "ANTHROPIC_API_KEY). 'claude-cli' delegates to the local Claude "
            "Code CLI via `claude -p` (uses the parent session's auth, no "
            "env var required)."
        ),
    )
    p_run.set_defaults(func=_cmd_run)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    # Same dual-module fix as `brain.invariants`: run the canonical
    # module so any decorator-based registries remain coherent.
    import brain.scenario as _canonical
    sys.exit(_canonical.main())
