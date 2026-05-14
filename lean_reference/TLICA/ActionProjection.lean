/-
TLICA.ActionProjection — Action-calibrated projected PCE.

This module adds an application-ready projected-PCE layer without changing the
deterministic foundation default in `TLICA.PCE`. The existing `PCE` remains
constant across actions by design. Here actions can differentiate only through
their projected future profiles, a future-MSI assignment, and a global ranking
on universal-domain content sets.

The projection remains deterministic, using `ProjectMap.project`. Stochastic
projection is deliberately deferred.
-/

import TLICA.MSI
import TLICA.ProfileIso
import TLICA.ProjectMap

namespace TLICA.ActionProjection

open TLICA.Profile TLICA.MSI TLICA.ProjectMap
open TLICA.ProfileIso

variable {α Act : Type*}

/-- A cross-time MSI assignment for projected profiles.

The model supplies an MSI for each projected scalar profile. We record
`domain_match`, not full profile equality, because full equality of
`ScalarProfile` values carries dependent function equality over subtype
domains. The action-projection layer only lifts future MSI contents into the
universal content type `α`, so domain agreement is the needed compatibility
condition here. -/
structure FutureMSIModel (α : Type*) where
  /-- The MSI assigned to a projected scalar profile. -/
  msiOf : ScalarProfile α → MSI α
  /-- The assigned MSI lives over the projected profile's content domain. -/
  domain_match : ∀ P, (msiOf P).profile.domain = P.domain

/-- Optional stronger cross-time MSI assignment requiring full profile
    isomorphism/coherence, not just domain agreement. Existing application
    layers continue to use `FutureMSIModel` by default. -/
structure CoherentFutureMSIModel (α : Type*) where
  /-- The MSI assigned to a projected scalar profile. -/
  msiOf : ScalarProfile α → MSI α
  /-- The assigned MSI profile is extensionally coherent with the projected
      profile. -/
  profile_iso : ∀ P, ProfileIso (msiOf P).profile P

namespace CoherentFutureMSIModel

/-- A coherent future-MSI model induces the weaker domain-match model used by
    the current action-projection stack. -/
def toFutureMSIModel (model : CoherentFutureMSIModel α) : FutureMSIModel α where
  msiOf := model.msiOf
  domain_match := by
    intro P
    ext x
    exact (model.profile_iso P).dom_iff x

/-- The weaker model induced by a coherent model has the expected domain match. -/
theorem toFutureMSIModel_domain_match
    (model : CoherentFutureMSIModel α) (P : ScalarProfile α) :
    ((model.toFutureMSIModel).msiOf P).profile.domain = P.domain :=
  (model.toFutureMSIModel).domain_match P

/-- The coherent profile isomorphism directly yields the weak domain-match
    condition used by `FutureMSIModel`. -/
theorem profile_iso_to_domain_match
    (model : CoherentFutureMSIModel α) (P : ScalarProfile α) :
    (model.msiOf P).profile.domain = P.domain := by
  ext x
  exact (model.profile_iso P).dom_iff x

/-- The weak model induced by a coherent model preserves the original MSI
    assignment. -/
theorem toFutureMSIModel_msiOf
    (model : CoherentFutureMSIModel α) (P : ScalarProfile α) :
    (model.toFutureMSIModel).msiOf P = model.msiOf P :=
  rfl

end CoherentFutureMSIModel

/-- A global preservation ranking over universal-domain content sets.

This is separate from `PreservationRanking`, whose rank is indexed over a
single MSI profile domain. The global ranking is the action-calibrated object
used to compare lifted future MSI contents across projected profiles. -/
structure GlobalPreservationRanking (α : Type*) where
  /-- Rank assigned to a universal-domain content set. -/
  rank : Set α → ℝ
  /-- Ranks are non-negative. -/
  rank_nonneg : ∀ S, 0 ≤ rank S
  /-- Ranking is monotone with respect to content-set inclusion. -/
  monotone : ∀ S T, S ⊆ T → rank S ≤ rank T

/-- Lift a set over a profile subtype domain into the universal content type. -/
def liftSet {α : Type*} {P : ScalarProfile α} (S : Set ↥P.domain) : Set α :=
  Subtype.val '' S

/-- Lift MSI contents into the universal content type. -/
def liftMSIContents {α : Type*} (msi : MSI α) : Set α :=
  Subtype.val '' msi.contents

/-- Deterministic projected profile for an action. -/
def projectedProfile (proj : ProjectMap α Act) (P : ScalarProfile α) (a : Act) :
    ScalarProfile α :=
  proj.project a P

/-- Future MSI assigned to the deterministic projected profile. -/
def futureMSI (fam : FutureMSIModel α) (proj : ProjectMap α Act)
    (P : ScalarProfile α) (a : Act) : MSI α :=
  fam.msiOf (projectedProfile proj P a)

/-- Universal-domain future content set used by projected PCE. -/
def futureMSIContents (fam : FutureMSIModel α) (proj : ProjectMap α Act)
    (P : ScalarProfile α) (a : Act) : Set α :=
  liftMSIContents (futureMSI fam proj P a)

/-- Action-calibrated projected PCE.

Unlike the deterministic foundation default `TLICA.PCE.PCE`, this value can
differentiate actions when the projected future MSI contents receive different
global ranks. -/
def ProjectedPCE (fam : FutureMSIModel α) (globalRank : GlobalPreservationRanking α)
    (proj : ProjectMap α Act) (P : ScalarProfile α) (a : Act) : ℝ :=
  globalRank.rank (futureMSIContents fam proj P a)

namespace ProjectedPCE

variable {α Act : Type*}

/-- Projected PCE is non-negative by global-rank non-negativity. -/
theorem nonneg (fam : FutureMSIModel α) (globalRank : GlobalPreservationRanking α)
    (proj : ProjectMap α Act) (P : ScalarProfile α) (a : Act) :
    0 ≤ ProjectedPCE fam globalRank proj P a :=
  globalRank.rank_nonneg _

/-- Equal lifted future MSI contents induce equal projected-PCE values. -/
theorem eq_of_future_contents_eq
    (fam : FutureMSIModel α) (globalRank : GlobalPreservationRanking α)
    (proj : ProjectMap α Act) (P : ScalarProfile α) (a b : Act)
    (h : futureMSIContents fam proj P a = futureMSIContents fam proj P b) :
    ProjectedPCE fam globalRank proj P a = ProjectedPCE fam globalRank proj P b := by
  unfold ProjectedPCE
  rw [h]

/-- If action `a`'s lifted future MSI contents are ranked at least action `b`'s,
    then projected PCE ranks `a` at least `b`. -/
theorem ge_of_rank_ge
    (fam : FutureMSIModel α) (globalRank : GlobalPreservationRanking α)
    (proj : ProjectMap α Act) (P : ScalarProfile α) (a b : Act)
    (h : globalRank.rank (futureMSIContents fam proj P b) ≤
      globalRank.rank (futureMSIContents fam proj P a)) :
    ProjectedPCE fam globalRank proj P b ≤ ProjectedPCE fam globalRank proj P a :=
  h

/-- Monotonicity of projected PCE with respect to lifted future MSI inclusion. -/
theorem monotone_of_future_contents_subset
    (fam : FutureMSIModel α) (globalRank : GlobalPreservationRanking α)
    (proj : ProjectMap α Act) (P : ScalarProfile α) (a b : Act)
    (h : futureMSIContents fam proj P b ⊆ futureMSIContents fam proj P a) :
    ProjectedPCE fam globalRank proj P b ≤ ProjectedPCE fam globalRank proj P a :=
  globalRank.monotone _ _ h

/-- Projected action-selection: `a` maximizes action-calibrated projected PCE. -/
def selectsProjectedAction
    (fam : FutureMSIModel α) (globalRank : GlobalPreservationRanking α)
    (proj : ProjectMap α Act) (P : ScalarProfile α) (a : Act) : Prop :=
  ∀ b : Act, ProjectedPCE fam globalRank proj P b ≤ ProjectedPCE fam globalRank proj P a

/-- A selected projected action has maximal projected PCE, by definition. -/
theorem selected_has_max_projectedPCE
    (fam : FutureMSIModel α) (globalRank : GlobalPreservationRanking α)
    (proj : ProjectMap α Act) (P : ScalarProfile α) (a b : Act)
    (hsel : selectsProjectedAction fam globalRank proj P a) :
    ProjectedPCE fam globalRank proj P b ≤ ProjectedPCE fam globalRank proj P a :=
  hsel b

/-- Conditional strict action differentiation by projected PCE.

No foundation-level claim is made that such actions exist. If an application
calibration supplies two actions whose lifted future MSI contents receive
strictly different global ranks, projected PCE strictly differentiates them. -/
theorem strictly_differentiates_of_rank_lt
    (fam : FutureMSIModel α) (globalRank : GlobalPreservationRanking α)
    (proj : ProjectMap α Act) (P : ScalarProfile α) (a b : Act)
    (h : globalRank.rank (futureMSIContents fam proj P a) <
      globalRank.rank (futureMSIContents fam proj P b)) :
    ProjectedPCE fam globalRank proj P a < ProjectedPCE fam globalRank proj P b :=
  h

end ProjectedPCE

end TLICA.ActionProjection
