/-
TLICA.MSI — The maximally-self-defined I.

Encodes §3 of the orphan_cluster_v0_1.md working paper: the maximally-self-defined
I (MSI) as a typed subset of the support-lived-I network, with foundation
axioms (cogito inclusion, lived-I containment, high-ρ density, closure under
PCE-equivalence).

The default functional form is Candidate 3.4.1 (threshold-based MSI).

Reference: 
  - 2_access_and_development.md §4.8 (theoretical statement).
  - orphan_cluster_v0_1.md §3 (foundation-ready definitions and axioms).
  - rosetta_stone_v0_2.md §12.3 (Rosetta-stone entry).
-/

import TLICA.Profile
import Mathlib.Data.Set.Basic

namespace TLICA.MSI

open TLICA.Profile
open Classical

variable {α : Type*}

/-- The maximally-self-defined I at modeling I `m` and time `t`, encoded
    as a subset of a profile's domain with the foundation axioms.

    For brevity here `α` plays the role of the universal content type;
    the MSI is parametric in a `ScalarProfile α` (which carries the
    lived-I-network-derived support and the cogito as a distinguished element).

    Reference: orphan_cluster_v0_1.md Definition 3.2.1. -/
structure MSI (α : Type*) where
  /-- The profile whose lived-I we are working over. -/
  profile : ScalarProfile α
  /-- The distinguished cogito element of `profile.domain`. -/
  cogito : ↥profile.domain
  /-- The cogito has profile value 1 (structural saturation). -/
  cogito_value : profile.toFun cogito = 1
  /-- The MSI contents as a subset of the profile's domain. -/
  contents : Set ↥profile.domain
  /-- **Axiom 3.3.1**: the cogito is in the MSI. -/
  cogito_in : cogito ∈ contents
  /-- The MSI threshold for non-cogito MSI members. -/
  threshold : ℝ
  /-- The threshold is strictly between 0 and 1. -/
  threshold_pos : 0 < threshold
  threshold_lt_one : threshold < 1
  /-- **Axiom 3.3.3**: high-ρ density on non-cogito MSI contents. -/
  density : ∀ x ∈ contents, x ≠ cogito → threshold ≤ profile.toFun x

namespace MSI

variable {α : Type*}

/-- The cogito has the maximum possible profile value (immediate from
    `cogito_value` and `profile.toFun_le_one`). -/
theorem cogito_is_supremum (msi : MSI α) :
    ∀ x : ↥msi.profile.domain, msi.profile.toFun x ≤ msi.profile.toFun msi.cogito := by
  intro x
  rw [msi.cogito_value]
  exact msi.profile.toFun_le_one x

/-- Every non-cogito MSI member has profile value at least the threshold. -/
theorem nonCogito_has_threshold_value (msi : MSI α) :
    ∀ x ∈ msi.contents, x ≠ msi.cogito → msi.threshold ≤ msi.profile.toFun x :=
  msi.density

/-- Every MSI member has positive profile value (since threshold > 0 and
    cogito has value 1). -/
theorem mem_msi_positive (msi : MSI α) :
    ∀ x ∈ msi.contents, 0 < msi.profile.toFun x := by
  intro x hx
  by_cases h : x = msi.cogito
  · rw [h, msi.cogito_value]
    norm_num
  · calc 0 < msi.threshold := msi.threshold_pos
      _ ≤ msi.profile.toFun x := msi.density x hx h

end MSI

end TLICA.MSI
