# docs/campaigns/

Per-phase archive of planning and execution artifacts. Each phase that
ran as a multi-step campaign has its own folder; older or ambiguous
historical artifacts live under `archive/`.

## Layout

| Path | What is in it |
|---|---|
| [`phase3_9/`](phase3_9/) | Phase 3.9 Persistent Session Store: SQLite-backed `/save-session` / `/load-session`, schema, dry run, audit. |
| [`phase3_10/`](phase3_10/) | Phase 3.10 Operational Hardening + Persistence Observability + Autosave (tracks 3.10a / 3.10b / 3.10c). Read-only verbs, one-shot CLI flags, autosave policy. |
| [`phase3_11/`](phase3_11/) | Phase 3.11 Comprehensive Live Behavior Test + Codex CLI Runtime Option. Live-launch / offline-interaction / persistence / autosave / DB-observability / LLM-runtime behavior reports plus the codex-cli runtime addition. |
| [`phase3_12/`](phase3_12/) | Phase 3.12 Coherent I-Loop Observatory: observatory report, Pattern Ledger, Coherence Monitor, and the SelfModel / Growth Ledger roadmap. |
| [`archive/`](archive/) | Older or pre-3.9 campaign artifacts: Phase 2 v1.x, Phase 3.1–3.8 / 3.8b, Operator TUI agent-layout work, Fast Safe Text Interaction, v0 plan corrigenda, ROADMAP_TEST, and other historical / ambiguous documents. |

## Phase 3.13 seed

[`phase3_12/PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md`](phase3_12/PHASE3_12_SELF_MODEL_GROWTH_LEDGER_ROADMAP.md)
is the **canonical seed document for a future Phase 3.13 Growth Ledger
campaign**. It was produced as Step 15 of the Phase 3.12 Coherent I-Loop
Observatory campaign and explicitly sits behind a Phase 3.12 Review Gate D.

A Phase 3.13 campaign should begin by reading that roadmap, the Phase
3.12 audit ([`phase3_12/PHASE3_12_COHERENT_I_LOOP_AUDIT.md`](phase3_12/PHASE3_12_COHERENT_I_LOOP_AUDIT.md)),
and the Pattern Ledger + Coherence Monitor synthesis / catalog-patch
plans in [`phase3_12/`](phase3_12/) — those are the closest active
prerequisites for any SelfModel / Growth Ledger work.

## Source-of-truth reminder

These are historical artifacts. Catalog rows, statuses, counts,
fixtures, and runtime behavior are governed by the live
[`INVARIANT_CATALOG.md`](../../INVARIANT_CATALOG.md) at the repo root,
not by anything in this directory.

If you are doing active mission work, start from
[`../../CURRENT_MISSION.md`](../../CURRENT_MISSION.md) and
[`../../CURRENT_CAMPAIGN.md`](../../CURRENT_CAMPAIGN.md), not from any
file here.
