# PHASE3_12_COHERENT_I_LOOP_MATRIX.md

## Purpose

Enumerate the Phase 3.12 existing-route behavior observations to execute before any new Pattern Ledger, Coherence Monitor, SelfModel, or Growth Ledger code is proposed.

```text
Status: LOCKED / MATRIX / NO-IMPLEMENTATION
Source: CURRENT_CAMPAIGN.md Step 4
Discipline: PHASE3_12_COHERENT_I_LOOP_KICKOFF.md
```

Verdicts must use only:

```text
works
awkward
confusing
fails
missing
blocked by env
ORS skipped
```

## Matrix rules

```text
SST = scripted subprocess or in-process dispatch test
MOT = manual observed test
RFI = read-only file inspection
ORS = optional real-LLM smoke
```

Step 6 should prefer SST through `LocalCommandLine.parse` + `OperatorSession.dispatch`.

---

## Baseline / launch / state

| ID | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|-------|------|----------------|----------|----------|----------|---------|
| 12.base.1 | SST | yes | `python3 -m tools.catalog counts` | Catalog v0.20 counts remain stable. | 214 / 83 / 9 / 12 / 16 |  |  |
| 12.base.2 | SST | yes | `bash tools/check_all.sh` | Standard gates pass before observations. | All checks passed. |  |  |
| 12.state.1 | SST | yes | fresh `OperatorSession(initial_state())` | Initial state has COGITO-only profile/MSI, tick=0, empty stream. | coherent baseline |  |  |

---

## Stream pattern observations

| ID | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|-------|------|----------------|----------|----------|----------|---------|
| 12.repetition.1 | SST | yes | repeated `/stream alpha alpha alpha` | Repeated stream chunks are accepted through bounded constructors. | chunks accepted; candidate count bounded |  |  |
| 12.repetition.2 | SST | yes | `/stream-summary` after repetition | Summary exposes stream count without kernel mutation. | read-only summary |  |  |
| 12.alternation.1 | SST | yes | `/stream alpha beta alpha beta` repeated | Alternating motif is recordable and distinct as text evidence. | chunks accepted |  |  |
| 12.novelty.1 | SST | yes | `/stream gamma novelty` after repetition | Novelty does not corrupt prior stream state. | new chunk/candidate accepted |  |  |
| 12.contradiction.1 | SST | yes | `/stream door=open`; `/stream door=closed` | Conflicting text remains raw evidence, not truth adjudication. | no direct PtCns mutation before promotion |  |  |

---

## Promotion / tick observations

| ID | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|-------|------|----------------|----------|----------|----------|---------|
| 12.candidates.1 | SST | yes | `/stream-candidates` | Candidate list is bounded and inspectable. | candidate IDs visible |  |  |
| 12.promote.1 | SST | yes | `/stream-promote <candidate_id>` | Candidate becomes queued percept only; no tick yet. | queue size increments |  |  |
| 12.step.1 | SST | yes | `/step` with offline client | Tick consumes queue head and mutates BrainState through public `tick()`. | tick_counter increments; latest_tick set |  |  |
| 12.state.2 | SST | yes | `/state` after tick | State view reports coherent profile/MSI/registry shape. | bounded state report |  |  |

---

## Saturation / failure path observations

| ID | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|-------|------|----------------|----------|----------|----------|---------|
| 12.saturation.1 | SST | yes | many repeated `/stream` inputs | Histories/candidates remain bounded. | no unbounded growth |  |  |
| 12.boundary.1 | SST | yes | over-length `/stream` input | Constructor/parser rejects locally. | bounded error; no state corruption |  |  |
| 12.failed-step.1 | SST | yes | `/step` with empty queue | Failed step preserves state. | bounded error; no mutation |  |  |

---

## Persistence / cold-start observations

| ID | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|-------|------|----------------|----------|----------|----------|---------|
| 12.persist.1 | SST | yes | `/save-session` after stream/promote/step | Saves kernel + stream state to temp DB. | DB created under `/tmp/phase3_12_*` |  |  |
| 12.persist.2 | SST | yes | `/load-session` into fresh session | Load reconstructs through public builders and invariants. | matching state fields |  |  |
| 12.persist.3 | SST | yes | `/session-status` after load | Status is bounded and truthful. | tick/stream counts match |  |  |

---

## Coherence-by-inspection observations

| ID | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|-------|------|----------------|----------|----------|----------|---------|
| 12.coherence.1 | RFI | yes | `brain/tick.py` | Runtime transition remains centralized in `tick()`. | no direct alternate transition found |  |  |
| 12.coherence.2 | RFI | yes | `brain/development/text_stream.py` | Text stream remains below truth/agency/tick. | no PtCns/tick/LLM dependency |  |  |
| 12.coherence.3 | RFI | yes | `brain/ui/session.py` | `/step` remains public tick route. | dispatch route confirmed |  |  |

---

## UX / interpretation observations

| ID | Style | Gate | Command / file | Contract | Expected | Observed | Verdict |
|----|-------|------|----------------|----------|----------|----------|---------|
| 12.ux.1 | MOT | env | inspect printed summaries/statuses | Operator can interpret what happened without reading source. | readable enough or classified awkward/confusing |  |  |
| 12.ux.2 | MOT | env | inspect repetition/alternation evidence | Pattern evidence is visible enough to support next Pattern Ledger design. | supports design or reveals gap |  |  |

## Step 6 report

Step 6 fills this matrix in:

```text
PHASE3_12_COHERENT_I_LOOP_OBSERVATORY_REPORT.md
```

No implementation is authorized by this matrix. It only authorizes observations over existing code.
