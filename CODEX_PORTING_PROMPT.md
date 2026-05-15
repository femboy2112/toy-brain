# CODEX_PORTING_PROMPT.md — Build Codex Analogs of the Claude Agents / Skills

## Purpose

You are Codex operating inside the `toy-brain` repository on the user's laptop.

Your task is to inspect the existing Claude configuration under `.claude/` and create Codex-side analogs so the user can switch between Claude Code and Codex without losing the project-specific workflows.

This is a **tooling/configuration port**, not a kernel feature.

Do **not** modify the TLICA kernel, scenario logic, invariant catalog, trace artifacts, or Lean reference files unless explicitly instructed by the user later.

---

## Source material

Read every relevant file under `.claude/`, especially:

```text
.claude/agents/
.claude/skills/
```

Expected Claude-side concepts currently include agents like:

```text
brain-explorer
brain-row-implementer
brain-runner-debugger
brain-spec-refresher
```

and the project skill:

```text
brain-invariants
```

Do not assume this list is complete. Inventory the actual `.claude/` tree first.

---

## Goal

Create Codex-compatible or Codex-readable analogs of the `.claude` agents and skills.

The result should let the user ask Codex to perform the same recurring repo workflows that Claude Code currently handles:

```text
read/navigate the TLICA catalog and Lean references
implement specific invariant rows
debug failing invariant rows
refresh the spec when upstream Lean changes
run and interpret the invariant tooling
preserve the v0.5 hardening discipline
prepare for Phase 3 planning without accidentally coding Phase 3 early
```

---

## Hard constraints

### 1. Do not change the kernel

Do not modify these paths unless the user explicitly asks:

```text
brain/tlica/
brain/tick.py
brain/invariants.py
brain/llm/
brain/trace.py
brain/fixtures/
INVARIANT_CATALOG.md
lean_reference/
traces/
scenarios/
```

This task is about Codex prompts/configuration only.

### 2. Do not change the catalog version

Current baseline is catalog v0.5. Do not bump it.

### 3. Do not start Phase 3 work

Do not implement the Osmotic Chamber, developmental substrate, output ladder, worldlet, Proto-BASIC REPL, expression layer, or language harness.

You may write prompts that help future agents plan Phase 3, but do not code Phase 3.

### 4. Do not invent Codex capabilities

If Codex has a native agents/skills format in this environment, use it.

If Codex does **not** expose a native agents/skills format, create a portable repo-local prompt pack instead.

Never claim a Codex feature exists unless it is visible in the local environment or documentation available to you.

### 5. Preserve Claude provenance

The Codex analogs should say they are derived from `.claude/` files and should point future maintainers back to the original Claude files as the source material.

---

## Recommended output structure

First inspect the local Codex environment. If there is an established Codex config convention in this repo or on the user's machine, follow it.

If no native convention is discoverable, create this portable structure:

```text
.codex/
├── README.md
├── agents/
│   ├── brain-explorer.md
│   ├── brain-row-implementer.md
│   ├── brain-runner-debugger.md
│   └── brain-spec-refresher.md
├── skills/
│   └── brain-invariants/
│       └── SKILL.md
└── CODEX_AGENT_MAP.md
```

If Codex requires a different location or filename format, adapt the structure and explain why in the final report.

---

## What each Codex analog should preserve

For each `.claude/agents/*.md` file, extract and preserve:

```text
agent name
intended trigger / when to use
allowed workflow
files it should read first
commands it may run
commands it must not run
scope boundaries
success criteria
final response style
```

For each `.claude/skills/**/SKILL.md` file, extract and preserve:

```text
skill name
purpose
tooling commands
catalog conventions
validation commands
refresh protocol
hard constraints
common failure modes
```

Where Claude-specific syntax exists, translate it into Codex-readable instructions without losing the operational intent.

---

## Required Codex-side roles

Create analogs for at least these roles if present in `.claude/agents/`.

### `brain-explorer`

Purpose:

```text
read-only navigator for Lean references, INVARIANT_CATALOG.md, traces, and docs
```

Must not modify files.

Expected commands / behaviors:

```bash
python -m tools.catalog list
python -m tools.catalog show I-XXX-NN
python -m tools.catalog counts
python -m tools.citations verify
grep / ripgrep over lean_reference/ and INVARIANT_CATALOG.md
```

### `brain-row-implementer`

Purpose:

```text
implement one specific catalog row or a small bounded range of rows
```

Must:

```text
read the catalog row
read the cited Lean source if any
read the owning module and fixture
make the smallest implementation change
run targeted row checks
run bash tools/check_all.sh before completion when practical
```

Must not:

```text
wander into unrelated rows
relax catalog requirements
change the catalog to make code pass unless the user explicitly requests a spec update
```

### `brain-runner-debugger`

Purpose:

```text
diagnose red invariant rows and propose/apply the smallest fix
```

Must:

```text
reproduce the failing row
read the row, fixture, owning module, and Lean source
identify whether the problem is constructor strictness, fixture invalidity, domain mismatch, Fraction/float leakage, catalog drift, or import/dependency violation
fix with minimum blast radius
```

### `brain-spec-refresher`

Purpose:

```text
apply SPEC_UPDATES.md when upstream lean-scratch changes
```

Must:

```text
respect upstream Lean > local lean_reference > catalog > Python code
never push to lean-scratch
classify declaration drift
update catalog rows only when justified
refresh lean_reference only after catalog review
run full health checks
```

---

## Required skill analog

Create a Codex-readable analog of `.claude/skills/brain-invariants/SKILL.md`.

It must include the v0.5 operational baseline:

```text
catalog v0.5
84 REQUIRED
15 STRUCTURAL
3 NOT-EXERCISED
12 DEFERRED
1 OBSERVED
```

It must include the core commands:

```bash
python -m tools.catalog counts
python -m tools.catalog list --status REQUIRED
python -m tools.catalog show I-XXX-NN
python -m tools.catalog generate-ids
python -m tools.citations verify
python -m tools.import_audit
python -m brain.invariants run
bash tools/check_all.sh
```

It must include the major hard rules:

```text
use Fraction in brain/tlica, brain/fixtures, brain/invariants
math.inf only for Lean top in dInfShared
Act is enum.Enum, not typing.Literal
ModeOp and Act are disjoint
agency.py must never import pce.py
Foundation PCE is action-constant; action selection uses feasibleProjectedPCE
COGITO_ID is reserved and never user-created
tick() is single-event in v1 semantics
trace is observation-only and SafeTracer-wrapped
catalog/registry coverage is enforced by I-CAT-01
```

---

## Validation requirements

After creating the Codex prompt/config files:

1. Show a concise tree of the created files.
2. Verify no forbidden kernel/catalog files were modified.
3. Run lightweight checks if available:

```bash
git diff --name-only
python -m tools.catalog counts
```

4. If you created only documentation/prompt files, do **not** run heavyweight or real-LLM scenario commands unless the user asks.
5. Do not run the real traced scenario as part of this task.

---

## Final report format

End with a short report:

```text
Created:
- path/to/file
- path/to/file

Mapped:
- Claude brain-explorer → Codex brain-explorer
- Claude brain-row-implementer → Codex brain-row-implementer
...

Validation:
- git diff --name-only: only .codex/ and this prompt pack changed
- catalog counts: pass / not run with reason

Notes:
- Any Codex-native assumptions
- Any files intentionally not ported
- Any follow-up needed
```

---

## Important project context

The repo is currently at the end of the v0.5 hardening cycle.

The branch merged to main included:

```text
catalog↔registry coverage audit
SafeTracer fail-open tracing
single-event tick guard
duplicate content_id rejection
ambiguous LLM parse rejection
FutureMSIModel runtime domain guard
strict catalog counts gate
real traced behavioral run artifacts
```

The real traced behavioral run showed kernel health was clean but semantic expectation match was 2/4. This supports the Phase 3 planning thesis:

```text
PRESERVE should be earned, not labeled.
```

Do not start coding Phase 3 from this prompt.

The next conceptual planning artifacts are:

```text
PHASE3_DEVELOPMENTAL_SYNTHESIS_v0.2.md
PHASE3_1_OSMOTIC_CHAMBER_KICKOFF.md
```

Those are planning tasks, not part of this Codex-port task unless the user explicitly asks.

---

## One-line instruction

Build Codex-side analogs of the existing `.claude` agents and skills, preserving their operational behavior and constraints, without changing the kernel, catalog, scenarios, traces, or Phase 3 implementation state.
