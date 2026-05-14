/-
TLICA — Lean 4 formalization of the Two-Layer Identity-Correlation Architecture.

This module is the top-level entry point. It imports every encoded submodule.

  Round 1 (rigorous edition v0.3.2 priority theorems):
    1. TLICA.Basic                                — KField typeclass.
    2. TLICA.IntegrationGraph                     — Lemma 2.4.2 (strict ρ-bound).
    3. TLICA.PhiCoordinate                        — Proposition 3.3.7.
    4. TLICA.ModeAggregation                      — Proposition 2.5.1.
    5. TLICA.Dynamics                             — Proposition 5.7.2.
    6. TLICA.NonReducibility                      — Theorem 6.5.1.

  Round 3 (profile-comparison apparatus):
    7. TLICA.Profile                              — Base ρ-profile structure.
    8. TLICA.ProfileComparison.Pointwise          — L^∞ shared and union distances.
    9. TLICA.ProfileComparison.ShellRefinement    — Shell-stratified bound.
    9b. TLICA.ProfileIso                          — Optional profile coherence relation.

  Round 4 (profile-comparison completion + foundation orphan cluster):
   10. TLICA.ProfileComparison.PseudoEMetric     — PseudoEMetricSpace instance.
   11. TLICA.MSI                                  — Maximally-self-defined I.
   12. TLICA.PreservationRanking                  — Π preservation-ranking.
   13. TLICA.PtCns                                — Prerogative of consistency.
   14. TLICA.Modes                                — Modes A, B, C as ModeOp.
	   15. TLICA.IBoundary                            — I/not-I boundary.
	   16. TLICA.ProjectMap                           — Future-state projection (deterministic).
	   17. TLICA.PCE                                  — Prerogative of continued existence.
	   18. TLICA.ActionProjection                     — Action-calibrated projected PCE.
	   19. TLICA.GeneralActionProjection              — Projected PCE over arbitrary action spaces.
	   20. TLICA.Agency                               — Feasible action selection under projected PCE.
	   21. TLICA.FreeWill                             — Branch-sensitive agency witnesses.
	   22. TLICA.TemporalTrajectory                   — Deterministic indexed profile trajectories.
	   23. TLICA.DifferentiatedAffect                 — Profile/PCE affect kernel.

The mapping from each Lean declaration to its location in the v0.3.2 rigorous
edition (or v0.2 working papers for round-3/4 declarations) is recorded in
`MAPPING.md` at the project root.
-/

import TLICA.Basic
import TLICA.IntegrationGraph
import TLICA.PhiCoordinate
import TLICA.ModeAggregation
import TLICA.Dynamics
import TLICA.NonReducibility
import TLICA.Profile
import TLICA.ProfileIso
import TLICA.ProfileComparison.Pointwise
import TLICA.ProfileComparison.ShellRefinement
import TLICA.ProfileComparison.PseudoEMetric
import TLICA.MSI
import TLICA.PreservationRanking
import TLICA.PtCns
import TLICA.Modes
import TLICA.IBoundary
import TLICA.ProjectMap
import TLICA.PCE
import TLICA.ActionProjection
import TLICA.GeneralActionProjection
import TLICA.Agency
import TLICA.FreeWill
import TLICA.TemporalTrajectory
import TLICA.DifferentiatedAffect
