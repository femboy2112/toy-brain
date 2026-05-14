# Lean source snapshot

This directory is a snapshot of the TLICA / TOCE Lean source at the time the v0.2 catalog was authored. It is **read-only reference material** for Claude Code to consult when implementing or auditing the Python kernel.

The canonical, evolving source is upstream at **https://github.com/femboy2112/lean-scratch** (read-only from this package's perspective). When the upstream changes, the catalog and this snapshot must be refreshed together — see `../SPEC_UPDATES.md` for the protocol.

## Contents

| Path | What it is |
|---|---|
| `TLICA.lean` | Top-level import aggregator. Lists every module imported by the rigorous edition. |
| `TLICA/Basic.lean` | The K-field typeclass (with the non-Archimedean δ that v0 drops). |
| `TLICA/Profile.lean` | `ScalarProfile` structure and `zeroExtend`. |
| `TLICA/MSI.lean` | Maximally-self-defined I; cogito axioms, density. |
| `TLICA/PtCns.lean` | Prerogative of consistency; three-valued evaluation, partition theorems. |
| `TLICA/Modes.lean` | `ModeOp` A/B/C/neutral; `fromEval` dispatch. |
| `TLICA/IBoundary.lean` | I/not-I boundary as derived from PtCns. |
| `TLICA/PreservationRanking.lean` | Π preservation-ranking, cogito-necessity axioms. |
| `TLICA/ProjectMap.lean` | Deterministic future-state projection; `identity_action_natural`. |
| `TLICA/PCE.lean` | Foundation-default prerogative of continued existence (action-constant). |
| `TLICA/ActionProjection.lean` | `FutureMSIModel`, `GlobalPreservationRanking`, action-sensitive `ProjectedPCE`. |
| `TLICA/Agency.lean` | `FeasibilityModel`, `AgencyContext`, selection theorems. |
| `TLICA/FreeWill.lean` | Branch-sensitive witnesses (surface only in v0; branch semantics deferred). |
| `TLICA/TemporalTrajectory.lean` | Deterministic trajectory, step distances, deferred-marker propositions. |
| `TLICA/DifferentiatedAffect.lean` | Affect kernel; PCE valence, affect-kernel witness, deferred markers. |
| `TLICA/IntegrationGraph.lean` | Strict ρ-bound (Lemma 2.4.2). |
| `TLICA/PhiCoordinate.lean` | φ-coordinate (deferred in v0; requires δ). |
| `TLICA/ModeAggregation.lean` | Convergence of mode-aggregation series (not exercised in v0). |
| `TLICA/Dynamics.lean` | Uniform convergence by M-test (not exercised in v0). |
| `TLICA/NonReducibility.lean` | Theorem 6.5.1 (deferred in v0; requires δ). |
| `TLICA/ProfileIso.lean` | Optional profile coherence relation. |
| `TLICA/ProfileComparison/Pointwise.lean` | `dInfShared`, `dInfUnion` and their pseudo-metric properties. |
| `TLICA/ProfileComparison/ShellRefinement.lean` | Shell-stratified bounds (not exercised in v0). |
| `TLICA/ProfileComparison/PseudoEMetric.lean` | `PseudoEMetricSpace` instance (not exercised in v0). |
| `TLICA/GeneralActionProjection.lean` | Compatibility aliases — **not** mirrored in Python. |
| `TOCE_Core.lean` | TOCE Boolean classifier layer; `ContentState`, `classifyContent`. |

## How the catalog cites these

The catalog references Lean declarations as `<file>::<decl>`, for example:

```
Profile.lean::ScalarProfile.toFun_nonneg
Agency.lean::AgencyWitness.selected_max
DifferentiatedAffect.lean::no_affectKernel_of_branch_and_pce_collapse
TemporalTrajectory.lean::stepSharedDistance_top_iff
PtCns.lean::partition_disjoint
```

To resolve a citation, open the corresponding file in this directory and search (`grep`, editor find) for the declaration name. Every catalog citation is verified to exist in this snapshot at the time of authoring.

## Reading order for a first-time pass

If you have never read this Lean code before, the most efficient onboarding path is:

1. `TLICA.lean` — the import list shows the full module shape.
2. `TLICA/Basic.lean` — the K-field, smallest module.
3. `TLICA/Profile.lean` — the central data structure.
4. `TLICA/MSI.lean` — the cogito anchor.
5. `TLICA/PtCns.lean` — the three-valued consistency evaluation.
6. `TLICA/Modes.lean` — how PtCns drives mode dispatch.
7. `TLICA/Agency.lean` — selection and `FeasibilityModel`.
8. `TLICA/ActionProjection.lean` — where action-sensitive PCE actually lives.
9. The rest as needed when implementing specific catalog rows.

## Do not modify

Files in this directory are reference. If you find what looks like a bug in the Lean (a stale comment, a name collision, a typo in a theorem statement), do **not** edit it locally — open an issue on `github.com/femboy2112/lean-scratch` instead, and let the canonical source resolve it. The local snapshot is only refreshed via the protocol in `../SPEC_UPDATES.md`.
