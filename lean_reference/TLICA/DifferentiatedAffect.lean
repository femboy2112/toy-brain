/-
TLICA.DifferentiatedAffect — Profile/PCE affect kernel.

This module adds the first generic differentiated-affect substrate over the
temporal trajectory, agency, and free-will layers. It formalizes only a
profile/PCE kernel: relative projected-PCE appraisal, branch-profile shift,
conditional affect witnesses, and bridges from free-will witnesses. It does not
encode named affect categories, empirical predictions, substrate pathways,
source-opacity pathways, stochastic projection, or phenomenological duration.
-/

import TLICA.TemporalTrajectory

namespace TLICA.DifferentiatedAffect

open TLICA.Profile
open TLICA.ProfileComparison.Pointwise
open TLICA.Agency
open TLICA.FreeWill
open TLICA.TemporalTrajectory
open TLICA.ActionProjection
open scoped ENNReal

variable {α Act : Type*}

/-- Projected-PCE delta of `action` relative to `baseline`. -/
def relativePCEDelta (ctx : AgencyContext α Act)
    (P : ScalarProfile α) (baseline action : Act) : ℝ :=
  feasibleProjectedPCE ctx P action - feasibleProjectedPCE ctx P baseline

/-- Positive projected-PCE valence relative to a baseline action. -/
def pceSupportive (ctx : AgencyContext α Act)
    (P : ScalarProfile α) (baseline action : Act) : Prop :=
  0 < relativePCEDelta ctx P baseline action

/-- Neutral projected-PCE valence relative to a baseline action. -/
def pceNeutral (ctx : AgencyContext α Act)
    (P : ScalarProfile α) (baseline action : Act) : Prop :=
  relativePCEDelta ctx P baseline action = 0

/-- Negative projected-PCE valence relative to a baseline action. -/
def pceDefeating (ctx : AgencyContext α Act)
    (P : ScalarProfile α) (baseline action : Act) : Prop :=
  relativePCEDelta ctx P baseline action < 0

/-- Supportive PCE valence is exactly strict improvement over the baseline. -/
theorem pceSupportive_iff
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (baseline action : Act) :
    pceSupportive ctx P baseline action ↔
      feasibleProjectedPCE ctx P baseline < feasibleProjectedPCE ctx P action := by
  unfold pceSupportive relativePCEDelta
  exact sub_pos

/-- Defeating PCE valence is exactly strict loss relative to the baseline. -/
theorem pceDefeating_iff
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (baseline action : Act) :
    pceDefeating ctx P baseline action ↔
      feasibleProjectedPCE ctx P action < feasibleProjectedPCE ctx P baseline := by
  unfold pceDefeating relativePCEDelta
  exact sub_neg

/-- Neutral PCE valence is exactly equality with the baseline. -/
theorem pceNeutral_iff
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (baseline action : Act) :
    pceNeutral ctx P baseline action ↔
      feasibleProjectedPCE ctx P action = feasibleProjectedPCE ctx P baseline := by
  unfold pceNeutral relativePCEDelta
  exact sub_eq_zero

/-- PCE valence relative to a baseline is supportive, neutral, or defeating. -/
theorem pceValence_trichotomy
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (baseline action : Act) :
    pceSupportive ctx P baseline action ∨
      pceNeutral ctx P baseline action ∨
        pceDefeating ctx P baseline action := by
  rcases lt_trichotomy (feasibleProjectedPCE ctx P baseline)
      (feasibleProjectedPCE ctx P action) with hlt | heq | hgt
  · left
    exact (pceSupportive_iff ctx P baseline action).2 hlt
  · right
    left
    exact (pceNeutral_iff ctx P baseline action).2 heq.symm
  · right
    right
    exact (pceDefeating_iff ctx P baseline action).2 hgt

/-- Supportive PCE valence excludes neutrality. -/
theorem pceSupportive_not_neutral
    {ctx : AgencyContext α Act} {P : ScalarProfile α} {baseline action : Act}
    (h : pceSupportive ctx P baseline action) :
    ¬ pceNeutral ctx P baseline action := by
  intro hn
  have hs := (pceSupportive_iff ctx P baseline action).1 h
  have hneut := (pceNeutral_iff ctx P baseline action).1 hn
  rw [hneut] at hs
  exact (lt_irrefl _ hs)

/-- Supportive PCE valence excludes defeating PCE valence. -/
theorem pceSupportive_not_defeating
    {ctx : AgencyContext α Act} {P : ScalarProfile α} {baseline action : Act}
    (h : pceSupportive ctx P baseline action) :
    ¬ pceDefeating ctx P baseline action := by
  intro hd
  have hs := (pceSupportive_iff ctx P baseline action).1 h
  have hdef := (pceDefeating_iff ctx P baseline action).1 hd
  exact (not_lt_of_gt hs) hdef

/-- Defeating PCE valence excludes neutrality. -/
theorem pceDefeating_not_neutral
    {ctx : AgencyContext α Act} {P : ScalarProfile α} {baseline action : Act}
    (h : pceDefeating ctx P baseline action) :
    ¬ pceNeutral ctx P baseline action := by
  intro hn
  have hd := (pceDefeating_iff ctx P baseline action).1 h
  have hneut := (pceNeutral_iff ctx P baseline action).1 hn
  rw [hneut] at hd
  exact (lt_irrefl _ hd)

/-- Union-domain distance between two deterministic action branches. -/
noncomputable def branchUnionDistance (ctx : AgencyContext α Act)
    (P : ScalarProfile α) (a b : Act) : ℝ≥0∞ :=
  dInfUnion (branchProfile ctx P a) (branchProfile ctx P b)

/-- Branch union distance is nonnegative by codomain. -/
theorem branchUnionDistance_nonneg
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (a b : Act) :
    0 ≤ branchUnionDistance ctx P a b :=
  bot_le

/-- Branch union distance is bounded by the union-distance profile bound. -/
theorem branchUnionDistance_le_one
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (a b : Act) :
    branchUnionDistance ctx P a b ≤ 1 := by
  unfold branchUnionDistance
  exact dInfUnion_le_one _ _

/-- Branch union distance is reflexive. -/
theorem branchUnionDistance_self
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (a : Act) :
    branchUnionDistance ctx P a a = 0 := by
  unfold branchUnionDistance
  exact dInfUnion_self _

/-- Branch union distance is symmetric. -/
theorem branchUnionDistance_symm
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (a b : Act) :
    branchUnionDistance ctx P a b = branchUnionDistance ctx P b a := by
  unfold branchUnionDistance
  exact dInfUnion_symm _ _

/-- Branch union distance satisfies the triangle inequality. -/
theorem branchUnionDistance_triangle
    (ctx : AgencyContext α Act) (P : ScalarProfile α) (a b c : Act) :
    branchUnionDistance ctx P a c ≤
      branchUnionDistance ctx P a b + branchUnionDistance ctx P b c := by
  unfold branchUnionDistance
  exact dInfUnion_triangle _ _ _

/-- Shared-domain distance between two deterministic action branches. -/
noncomputable def branchSharedDistance (ctx : AgencyContext α Act)
    (P : ScalarProfile α) (a b : Act) : ℝ≥0∞ :=
  dInfShared (branchProfile ctx P a) (branchProfile ctx P b)

/-- Equality-based branch-profile shift predicate. -/
def branchProfileShift (ctx : AgencyContext α Act)
    (P : ScalarProfile α) (a b : Act) : Prop :=
  branchProfile ctx P a ≠ branchProfile ctx P b

/-- Equal branch profiles have equal future-content sets. -/
theorem branchFutureContents_eq_of_branchProfile_eq
    {ctx : AgencyContext α Act} {P : ScalarProfile α} {a b : Act}
    (h : branchProfile ctx P a = branchProfile ctx P b) :
    branchFutureContents ctx P a = branchFutureContents ctx P b := by
  unfold branchProfile at h
  unfold branchFutureContents futureMSIContents futureMSI
  rw [h]

/-- Distinct branch future contents imply distinct branch profiles. -/
theorem branchProfile_ne_of_branchFutureContents_ne
    {ctx : AgencyContext α Act} {P : ScalarProfile α} {a b : Act}
    (h : branchFutureContents ctx P a ≠ branchFutureContents ctx P b) :
    branchProfile ctx P a ≠ branchProfile ctx P b := by
  intro hprofile
  exact h (branchFutureContents_eq_of_branchProfile_eq hprofile)

/-- A PCE-support affect witness over feasible actions. -/
structure PCESupportAffectWitness
    (ctx : AgencyContext α Act) (P : ScalarProfile α) where
  baseline : Act
  action : Act
  baseline_feasible : baseline ∈ ctx.feasible P
  action_feasible : action ∈ ctx.feasible P
  support : pceSupportive ctx P baseline action

/-- A PCE-defeat affect witness over feasible actions. -/
structure PCEDefeatAffectWitness
    (ctx : AgencyContext α Act) (P : ScalarProfile α) where
  baseline : Act
  action : Act
  baseline_feasible : baseline ∈ ctx.feasible P
  action_feasible : action ∈ ctx.feasible P
  defeat : pceDefeating ctx P baseline action

/-- A PCE-neutral affect witness over feasible actions. -/
structure PCENeutralAffectWitness
    (ctx : AgencyContext α Act) (P : ScalarProfile α) where
  baseline : Act
  action : Act
  baseline_feasible : baseline ∈ ctx.feasible P
  action_feasible : action ∈ ctx.feasible P
  neutral : pceNeutral ctx P baseline action

/-- A profile-shift affect witness over feasible action branches. -/
structure ProfileShiftAffectWitness
    (ctx : AgencyContext α Act) (P : ScalarProfile α) where
  baseline : Act
  action : Act
  baseline_feasible : baseline ∈ ctx.feasible P
  action_feasible : action ∈ ctx.feasible P
  profile_shift : branchProfileShift ctx P baseline action

/-- Minimal structural affect-kernel witness: either branch-profile shift or
    projected-PCE differentiation between feasible actions. -/
structure AffectKernelWitness
    (ctx : AgencyContext α Act) (P : ScalarProfile α) where
  baseline : Act
  action : Act
  baseline_feasible : baseline ∈ ctx.feasible P
  action_feasible : action ∈ ctx.feasible P
  structural_perturbation :
    branchProfileShift ctx P baseline action ∨
      feasibleProjectedPCE ctx P baseline ≠ feasibleProjectedPCE ctx P action

/-- PCE support gives a generic affect-kernel witness. -/
def affectKernel_of_pceSupport
    {ctx : AgencyContext α Act} {P : ScalarProfile α}
    (w : PCESupportAffectWitness ctx P) :
    AffectKernelWitness ctx P where
  baseline := w.baseline
  action := w.action
  baseline_feasible := w.baseline_feasible
  action_feasible := w.action_feasible
  structural_perturbation := by
    right
    have hlt := (pceSupportive_iff ctx P w.baseline w.action).1 w.support
    exact ne_of_lt hlt

/-- PCE defeat gives a generic affect-kernel witness. -/
def affectKernel_of_pceDefeat
    {ctx : AgencyContext α Act} {P : ScalarProfile α}
    (w : PCEDefeatAffectWitness ctx P) :
    AffectKernelWitness ctx P where
  baseline := w.baseline
  action := w.action
  baseline_feasible := w.baseline_feasible
  action_feasible := w.action_feasible
  structural_perturbation := by
    right
    have hlt := (pceDefeating_iff ctx P w.baseline w.action).1 w.defeat
    exact (ne_of_gt hlt)

/-- Branch-profile shift gives a generic affect-kernel witness. -/
def affectKernel_of_profileShift
    {ctx : AgencyContext α Act} {P : ScalarProfile α}
    (w : ProfileShiftAffectWitness ctx P) :
    AffectKernelWitness ctx P where
  baseline := w.baseline
  action := w.action
  baseline_feasible := w.baseline_feasible
  action_feasible := w.action_feasible
  structural_perturbation := Or.inl w.profile_shift

/-- A free-will witness gives a profile-shift affect witness. -/
def profileShiftAffectWitness_of_freeWillWitness
    {ctx : AgencyContext α Act} {P : ScalarProfile α}
    (w : FreeWillWitness ctx P) :
    ProfileShiftAffectWitness ctx P where
  baseline := w.selected
  action := w.alternative
  baseline_feasible := w.selected_agency.1
  action_feasible := w.alternative_live.2.1
  profile_shift := branchProfile_ne_of_branchFutureContents_ne w.branch_distinct

/-- A free-will witness gives a generic affect-kernel witness through
    branch-profile shift. -/
def affectKernel_of_freeWillWitness
    {ctx : AgencyContext α Act} {P : ScalarProfile α}
    (w : FreeWillWitness ctx P) :
    AffectKernelWitness ctx P :=
  affectKernel_of_profileShift (profileShiftAffectWitness_of_freeWillWitness w)

/-- A PCE-differentiated free-will witness gives a generic affect-kernel
    witness through projected-PCE differentiation. -/
def affectKernel_of_pceFreeWillWitness
    {ctx : AgencyContext α Act} {P : ScalarProfile α}
    (w : PCEFreeWillWitness ctx P) :
    AffectKernelWitness ctx P where
  baseline := w.selected
  action := w.alternative
  baseline_feasible := w.selected_agency.1
  action_feasible := w.alternative_live.2.1
  structural_perturbation := Or.inr w.pce_distinct

/-- If feasible branches collapse both in profile and projected-PCE value, then
    no affect-kernel witness exists. -/
theorem no_affectKernel_of_branch_and_pce_collapse
    (ctx : AgencyContext α Act) (P : ScalarProfile α)
    (hprofile : ∀ a b, a ∈ ctx.feasible P → b ∈ ctx.feasible P →
      branchProfile ctx P a = branchProfile ctx P b)
    (hpce : ∀ a b, a ∈ ctx.feasible P → b ∈ ctx.feasible P →
      feasibleProjectedPCE ctx P a = feasibleProjectedPCE ctx P b) :
    ¬ ∃ _w : AffectKernelWitness ctx P, True := by
  intro hw
  rcases hw with ⟨w, _hw_true⟩
  rcases w.structural_perturbation with hshift | hpce_ne
  · exact hshift (hprofile w.baseline w.action w.baseline_feasible w.action_feasible)
  · exact hpce_ne (hpce w.baseline w.action w.baseline_feasible w.action_feasible)

/-- Naming bridge: temporal affect intensity as adjacent union-profile change. -/
noncomputable def temporalAffectIntensity
    (traj : ProfileTrajectory α) (n : ℕ) : ℝ≥0∞ :=
  stepUnionDistance traj n

/-- Temporal affect intensity is nonnegative by codomain. -/
theorem temporalAffectIntensity_nonneg
    (traj : ProfileTrajectory α) (n : ℕ) :
    0 ≤ temporalAffectIntensity traj n :=
  bot_le

/-- Union-step stability bounds temporal affect intensity. -/
theorem temporalAffectIntensity_le_of_unionStepStable
    {traj : ProfileTrajectory α} {ε : ℝ≥0∞}
    (h : unionStepStable traj ε) (n : ℕ) :
    temporalAffectIntensity traj n ≤ ε :=
  h n

/-- Temporal affect intensity is bounded by the union-distance profile bound. -/
theorem temporalAffectIntensity_le_one
    (traj : ProfileTrajectory α) (n : ℕ) :
    temporalAffectIntensity traj n ≤ 1 := by
  unfold temporalAffectIntensity
  exact stepUnionDistance_le_one traj n

/-- PCE-support witnesses are necessarily PCE-non-neutral. -/
theorem pceSupportAffectWitness_pce_ne
    {ctx : AgencyContext α Act} {P : ScalarProfile α}
    (w : PCESupportAffectWitness ctx P) :
    feasibleProjectedPCE ctx P w.baseline ≠ feasibleProjectedPCE ctx P w.action := by
  have hlt := (pceSupportive_iff ctx P w.baseline w.action).1 w.support
  exact ne_of_lt hlt

/-- Deferred marker: named affect taxonomy is not formalized in this kernel.
    This is not a theorem claim. -/
def namedAffectTaxonomy_deferred : Prop := True

/-- Deferred marker: love as constitutive extension is not formalized here.
    This is not a theorem claim. -/
def loveConstitutiveExtension_deferred : Prop := True

/-- Deferred marker: substrate affect pathways are not formalized here.
    This is not a theorem claim. -/
def substrateAffectPathway_deferred : Prop := True

/-- Deferred marker: source-opacity affect is not formalized here.
    This is not a theorem claim. -/
def sourceOpacityAffect_deferred : Prop := True

end TLICA.DifferentiatedAffect
