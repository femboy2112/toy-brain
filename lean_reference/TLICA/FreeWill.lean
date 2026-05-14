/-
TLICA.FreeWill — Branch-sensitive agency witnesses.

This module adds the first free-will layer over `TLICA.Agency`. Free will is
not identified with bare agency or unconditioned randomness. Here it is modeled
as agency with live feasible alternatives and branch-sensitive projected
outcomes. The module provides witness structures and conditional theorems only;
it does not assert that free will exists globally.

Stochastic projection remains deferred.
-/

import TLICA.Agency

namespace TLICA.FreeWill

open TLICA.Profile
open TLICA.Agency
open TLICA.ActionProjection

variable {α Act : Type*}

/-- The projected branch profile for an action in an agency context. -/
def branchProfile (ctx : AgencyContext α Act) (P : ScalarProfile α) (a : Act) :
    ScalarProfile α :=
  projectedProfile ctx.proj P a

/-- Branch profiles are definitionally the direct projected profiles. -/
theorem branchProfile_eq_projectedProfile
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (a : Act) :
    branchProfile ctx P a = projectedProfile ctx.proj P a :=
  rfl

/-- The lifted future MSI contents for an action branch. -/
def branchFutureContents (ctx : AgencyContext α Act)
    (P : ScalarProfile α) (a : Act) : Set α :=
  futureMSIContents ctx.fam ctx.proj P a

/-- Branch future contents are definitionally the direct future-MSI contents. -/
theorem branchFutureContents_eq_futureMSIContents
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (a : Act) :
    branchFutureContents ctx P a =
      futureMSIContents ctx.fam ctx.proj P a :=
  rfl

/-- Live alternatives whose projected future contents differ. -/
def branchDistinctAlternative (ctx : AgencyContext α Act)
    (P : ScalarProfile α) (a b : Act) : Prop :=
  liveAlternative ctx P a b ∧
    branchFutureContents ctx P a ≠ branchFutureContents ctx P b

/-- Live alternatives whose projected-PCE values differ. -/
def pceBranchDistinctAlternative (ctx : AgencyContext α Act)
    (P : ScalarProfile α) (a b : Act) : Prop :=
  liveAlternative ctx P a b ∧
    feasibleProjectedPCE ctx P a ≠ feasibleProjectedPCE ctx P b

/-- The set of currently open alternatives, used as a Rosetta naming bridge. -/
def openAlternatives (ctx : AgencyContext α Act) (P : ScalarProfile α) : Set Act :=
  {a | a ∈ ctx.feasible P}

/-- If two branches have different projected-PCE values, their lifted future
    contents cannot be equal. -/
theorem branchFutureContents_ne_of_pce_ne
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (a b : Act)
    (h : feasibleProjectedPCE ctx P a ≠ feasibleProjectedPCE ctx P b) :
    branchFutureContents ctx P a ≠ branchFutureContents ctx P b := by
  intro hcontents
  apply h
  have hfuture :
      futureMSIContents ctx.fam ctx.proj P a =
        futureMSIContents ctx.fam ctx.proj P b := by
    simpa [branchFutureContents] using hcontents
  unfold feasibleProjectedPCE ProjectedPCE
  change ctx.globalRank.rank (futureMSIContents ctx.fam ctx.proj P a) =
    ctx.globalRank.rank (futureMSIContents ctx.fam ctx.proj P b)
  rw [hfuture]

/-- PCE-branch distinct alternatives are branch-distinct alternatives. -/
theorem branchDistinctAlternative_of_pceBranchDistinctAlternative
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (a b : Act)
    (h : pceBranchDistinctAlternative ctx P a b) :
    branchDistinctAlternative ctx P a b :=
  ⟨h.1, branchFutureContents_ne_of_pce_ne ctx P a b h.2⟩

/-- Free-will witness: selected agency plus a live feasible alternative whose
    projected future contents differ from the selected branch. -/
structure FreeWillWitness (ctx : AgencyContext α Act) (P : ScalarProfile α) where
  /-- The selected action. -/
  selected : Act
  /-- The selected action satisfies agency selection. -/
  selected_agency : selectsFeasibleAction ctx P selected
  /-- A live alternative action. -/
  alternative : Act
  /-- The selected action and alternative are distinct feasible actions. -/
  alternative_live : liveAlternative ctx P selected alternative
  /-- The selected and alternative branches have distinct future contents. -/
  branch_distinct :
    branchFutureContents ctx P selected ≠ branchFutureContents ctx P alternative

/-- PCE-differentiated free-will witness: selected agency plus a live feasible
    alternative with a distinct projected-PCE value. This is stronger than
    branch-distinct free will. -/
structure PCEFreeWillWitness (ctx : AgencyContext α Act) (P : ScalarProfile α) where
  /-- The selected action. -/
  selected : Act
  /-- The selected action satisfies agency selection. -/
  selected_agency : selectsFeasibleAction ctx P selected
  /-- A live alternative action. -/
  alternative : Act
  /-- The selected action and alternative are distinct feasible actions. -/
  alternative_live : liveAlternative ctx P selected alternative
  /-- The selected and alternative branches have distinct projected-PCE values. -/
  pce_distinct :
    feasibleProjectedPCE ctx P selected ≠ feasibleProjectedPCE ctx P alternative

namespace FreeWillWitness

variable {ctx : AgencyContext α Act} {P : ScalarProfile α}

/-- A free-will witness implies live feasible alternatives. -/
theorem hasLiveAlternatives (w : FreeWillWitness ctx P) :
    hasLiveAlternatives ctx P :=
  ⟨w.selected, w.alternative, w.alternative_live⟩

/-- A free-will witness yields two distinct feasible actions. -/
theorem exists_distinct_feasible (w : FreeWillWitness ctx P) :
    ∃ a b, a ∈ ctx.feasible P ∧ b ∈ ctx.feasible P ∧ a ≠ b :=
  exists_distinct_feasible_of_hasLiveAlternatives ctx P w.hasLiveAlternatives

/-- A free-will witness packages a branch-distinct alternative. -/
theorem branchDistinctAlternative (w : FreeWillWitness ctx P) :
    branchDistinctAlternative ctx P w.selected w.alternative :=
  ⟨w.alternative_live, w.branch_distinct⟩

end FreeWillWitness

namespace PCEFreeWillWitness

variable {ctx : AgencyContext α Act} {P : ScalarProfile α}

/-- PCE-differentiated free will is formally stronger than branch-distinct
    free will. -/
def toFreeWillWitness (w : PCEFreeWillWitness ctx P) :
    FreeWillWitness ctx P where
  selected := w.selected
  selected_agency := w.selected_agency
  alternative := w.alternative
  alternative_live := w.alternative_live
  branch_distinct :=
    branchFutureContents_ne_of_pce_ne ctx P w.selected w.alternative w.pce_distinct

/-- A PCE-differentiated free-will witness implies live alternatives. -/
theorem hasLiveAlternatives (w : PCEFreeWillWitness ctx P) :
    hasLiveAlternatives ctx P :=
  w.toFreeWillWitness.hasLiveAlternatives

/-- A PCE-differentiated free-will witness implies a PCE-differentiated
    feasible alternative in the agency layer. -/
theorem pceDifferentiatedAlternative (w : PCEFreeWillWitness ctx P) :
    pceDifferentiatedAlternative ctx P w.selected w.alternative := by
  exact ⟨w.alternative_live.1, w.alternative_live.2.1, w.pce_distinct⟩

/-- A PCE-differentiated free-will witness packages a PCE-branch-distinct
    alternative. -/
theorem pceBranchDistinctAlternative (w : PCEFreeWillWitness ctx P) :
    pceBranchDistinctAlternative ctx P w.selected w.alternative :=
  ⟨w.alternative_live, w.pce_distinct⟩

end PCEFreeWillWitness

/-- PCE-differentiated free will is formally stronger than branch-distinct
    free will. -/
def freeWillWitness_of_pceFreeWillWitness
    (ctx : AgencyContext α Act) (P : ScalarProfile α)
    (w : PCEFreeWillWitness ctx P) :
    FreeWillWitness ctx P :=
  w.toFreeWillWitness

/-- If a selected action strictly beats a feasible live alternative in
    projected PCE, then a PCE-differentiated free-will witness exists. -/
def pceFreeWillWitness_of_selected_strictly_beats
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (selected alternative : Act)
    (hsel : selectsFeasibleAction ctx P selected)
    (hlive : liveAlternative ctx P selected alternative)
    (hgt : feasibleProjectedPCE ctx P alternative <
      feasibleProjectedPCE ctx P selected) :
    PCEFreeWillWitness ctx P where
  selected := selected
  selected_agency := hsel
  alternative := alternative
  alternative_live := hlive
  pce_distinct := ne_of_gt hgt

/-- If a selected action strictly beats a feasible live alternative in
    projected PCE, then a branch-distinct free-will witness exists. -/
def freeWillWitness_of_selected_strictly_beats
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (selected alternative : Act)
    (hsel : selectsFeasibleAction ctx P selected)
    (hlive : liveAlternative ctx P selected alternative)
    (hgt : feasibleProjectedPCE ctx P alternative <
      feasibleProjectedPCE ctx P selected) :
    FreeWillWitness ctx P :=
  freeWillWitness_of_pceFreeWillWitness ctx P
    (pceFreeWillWitness_of_selected_strictly_beats ctx P selected alternative hsel hlive hgt)

/-- If all feasible actions have equal branch future contents, then no
    branch-distinct free-will witness exists. -/
theorem no_freeWillWitness_of_all_branch_contents_equal
    (ctx : AgencyContext α Act) (P : ScalarProfile α)
    (h : ∀ a b, a ∈ ctx.feasible P → b ∈ ctx.feasible P →
      branchFutureContents ctx P a = branchFutureContents ctx P b) :
    ¬ ∃ _w : FreeWillWitness ctx P, True := by
  intro hw
  rcases hw with ⟨w, _hw_true⟩
  have h_selected : w.selected ∈ ctx.feasible P := w.selected_agency.1
  have h_alternative : w.alternative ∈ ctx.feasible P := w.alternative_live.2.1
  exact w.branch_distinct (h w.selected w.alternative h_selected h_alternative)

/-- Branch collapse also excludes PCE-differentiated free-will witnesses. -/
theorem no_pceFreeWillWitness_of_all_branch_contents_equal
    (ctx : AgencyContext α Act) (P : ScalarProfile α)
    (h : ∀ a b, a ∈ ctx.feasible P → b ∈ ctx.feasible P →
      branchFutureContents ctx P a = branchFutureContents ctx P b) :
    ¬ ∃ _w : PCEFreeWillWitness ctx P, True := by
  intro hw
  rcases hw with ⟨w, hw_true⟩
  exact no_freeWillWitness_of_all_branch_contents_equal ctx P h
    ⟨freeWillWitness_of_pceFreeWillWitness ctx P w, hw_true⟩

/-- PCE collapse excludes PCE-differentiated free-will witnesses. -/
theorem no_pceFreeWillWitness_of_all_pce_equal
    (ctx : AgencyContext α Act) (P : ScalarProfile α)
    (h : ∀ a b, a ∈ ctx.feasible P → b ∈ ctx.feasible P →
      feasibleProjectedPCE ctx P a = feasibleProjectedPCE ctx P b) :
    ¬ ∃ _w : PCEFreeWillWitness ctx P, True := by
  intro hw
  rcases hw with ⟨w, _hw_true⟩
  have h_selected : w.selected ∈ ctx.feasible P := w.selected_agency.1
  have h_alternative : w.alternative ∈ ctx.feasible P := w.alternative_live.2.1
  exact w.pce_distinct (h w.selected w.alternative h_selected h_alternative)

end TLICA.FreeWill
