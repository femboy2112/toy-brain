/-
TLICA.PtCns — The prerogative of consistency.

Encodes §7 of the orphan_cluster_v0_1.md working paper: PtCns as an
evaluation function from contents to a three-element consistency-evaluation
space, with foundation axioms (cogito invariance, asymmetric framing, mode
triggering, consistency-standard preservation).

Reference:
  - 2_access_and_development.md §4.2, §4.8 (theoretical statement).
  - 4_derived_concepts_and_predictions.md §9.5 (inter-I generalization).
  - orphan_cluster_v0_1.md §7 (foundation-ready definitions and axioms).
-/

import TLICA.MSI

namespace TLICA.PtCns

open TLICA.Profile TLICA.MSI

/-- The three-element consistency-evaluation space.

    * `damage` (corresponds to −1): integrating the content would damage
      frame consistency; Mode A differentiation is the structural response.
    * `neutral` (corresponds to 0): identity-neutral encapsulation;
      content is registered but bounded as non-self-defining.
    * `preserve` (corresponds to +1): integrating the content would preserve
      or extend frame consistency; Mode C integration is the structural response.

    Reference: orphan_cluster_v0_1.md §7.2.1. -/
inductive ConsistencyEval where
  | damage
  | neutral
  | preserve
  deriving DecidableEq, Repr

namespace ConsistencyEval

/-- Mapping to integer values for clarity in proofs and statements. -/
def toInt : ConsistencyEval → ℤ
  | damage => -1
  | neutral => 0
  | preserve => 1

@[simp] theorem toInt_damage : toInt damage = -1 := rfl
@[simp] theorem toInt_neutral : toInt neutral = 0 := rfl
@[simp] theorem toInt_preserve : toInt preserve = 1 := rfl

end ConsistencyEval

variable {α : Type*}

/-- The prerogative of consistency for a modeling I, parameterized by an MSI
    (which carries the cogito and the I's frame structure).

    Reference: orphan_cluster_v0_1.md Definition 7.2.1. -/
structure PtCns (msi : MSI α) where
  /-- The evaluation function on contents in the profile's domain. -/
  eval : ↥msi.profile.domain → ConsistencyEval
  /-- **Axiom 7.3.1**: the cogito is always evaluated as preserving. -/
  cogito_invariance : eval msi.cogito = ConsistencyEval.preserve

namespace PtCns

variable {α : Type*}

/-- The set of PtCns-positive contents (those eliciting Mode C integration). -/
def positiveContents (msi : MSI α) (p : PtCns msi) : Set ↥msi.profile.domain :=
  {x | p.eval x = ConsistencyEval.preserve}

/-- The set of PtCns-negative contents (those eliciting Mode A differentiation). -/
def negativeContents (msi : MSI α) (p : PtCns msi) : Set ↥msi.profile.domain :=
  {x | p.eval x = ConsistencyEval.damage}

/-- The set of PtCns-neutral contents (identity-neutral encapsulation). -/
def neutralContents (msi : MSI α) (p : PtCns msi) : Set ↥msi.profile.domain :=
  {x | p.eval x = ConsistencyEval.neutral}

/-- The cogito is in the PtCns-positive set, by cogito invariance. -/
theorem cogito_in_positive (msi : MSI α) (p : PtCns msi) :
    msi.cogito ∈ p.positiveContents := by
  unfold positiveContents
  simp [Set.mem_setOf_eq, p.cogito_invariance]

/-- The cogito is not PtCns-negative. -/
theorem cogito_not_negative (msi : MSI α) (p : PtCns msi) :
    msi.cogito ∉ p.negativeContents := by
  unfold negativeContents
  simp [Set.mem_setOf_eq, p.cogito_invariance]

/-- The cogito is not PtCns-neutral. -/
theorem cogito_not_neutral (msi : MSI α) (p : PtCns msi) :
    msi.cogito ∉ p.neutralContents := by
  unfold neutralContents
  simp [Set.mem_setOf_eq, p.cogito_invariance]

/-- The three partition sets cover the domain disjointly. -/
theorem partition_disjoint (msi : MSI α) (p : PtCns msi) :
    p.positiveContents ∩ p.negativeContents = ∅ ∧
    p.positiveContents ∩ p.neutralContents = ∅ ∧
    p.negativeContents ∩ p.neutralContents = ∅ := by
  refine ⟨?_, ?_, ?_⟩
  all_goals {
    ext x
    simp [positiveContents, negativeContents, neutralContents, Set.mem_inter_iff,
          Set.mem_empty_iff_false]
    intro h1 h2
    rw [h1] at h2
    cases h2
  }

/-- The three PtCns evaluation classes cover the full profile domain. -/
theorem partition_cover (msi : MSI α) (p : PtCns msi) :
    p.positiveContents ∪ p.negativeContents ∪ p.neutralContents = Set.univ := by
  ext x
  simp [positiveContents, negativeContents, neutralContents]
  cases h : p.eval x <;> simp [h]

end PtCns

end TLICA.PtCns
