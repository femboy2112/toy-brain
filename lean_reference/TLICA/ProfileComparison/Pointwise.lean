/-
TLICA.ProfileComparison.Pointwise — Pointwise (L^∞) profile distances.

This module encodes the subdomain-restriction L^∞ shared and union
distances of Definitions 5.1.1 and 5.2bis.1 in the v0.2 profile-comparison
working paper. Both are valued in `ℝ≥0∞` (extended non-negative reals,
`ENNReal` in mathlib) so that:

* the union form's supremum is always well-defined (the universe `α` is the
  natural index set, and `ENNReal`'s `iSup` is well-defined regardless of
  boundedness);

* the shared form's `+∞` convention on empty intersection is encoded
  cleanly using `ENNReal`'s `⊤` element.

The pseudo-metric structure of each form is established by Propositions
5.2.1–5.2.6 of the v0.2 paper:

* non-negativity, symmetry, and reflexivity (both forms);
* identity of indiscernibles (partial for shared form; full for union form);
* qualified triangle inequality (shared form);
* unqualified triangle inequality (union form).

Reference: v0.3.1 rigorous edition + profile_comparison_v0_2.md,
  - §5.1 (subdomain-restriction L^∞ shared distance).
  - §5.2 (pseudo-metric structure of the shared form).
  - §5.2bis (union form via zero-extension).
  - §5.3 (connections to shells, lived-I, persistence).
-/

import TLICA.Profile
import Mathlib.Data.ENNReal.Basic
import Mathlib.Data.ENNReal.Real
import Mathlib.Tactic.Linarith

namespace TLICA.ProfileComparison.Pointwise

open TLICA.Profile
open Classical
open scoped ENNReal

variable {α : Type*}

/-! ## The union form distance via zero-extension -/

/-- **Definition 5.2bis.1**: the $L^\infty$ union distance via zero-extension.

    The supremum is over the universal content-type `α`, using the
    zero-extensions of both profiles. Outside `f.domain ∪ g.domain`, both
    extensions are zero and the contribution to the supremum is zero;
    thus this definition is equivalent to the paper's "sup over A ∪ A'"
    formulation but is cleaner in Lean because the indexing type is fixed.

    Reference: profile_comparison_v0_2.md §5.2bis.1. -/
noncomputable def dInfUnion (f g : ScalarProfile α) : ℝ≥0∞ :=
  ⨆ x : α, ENNReal.ofReal |f.zeroExtend x - g.zeroExtend x|

/-! ### Basic properties of the union form -/

/-- **Proposition 5.2.1** (non-negativity, union form).
    Trivial by codomain. -/
theorem dInfUnion_nonneg (f g : ScalarProfile α) : 0 ≤ dInfUnion f g :=
  bot_le

/-- **Proposition 5.2.2** (symmetry, union form). -/
theorem dInfUnion_symm (f g : ScalarProfile α) : dInfUnion f g = dInfUnion g f := by
  unfold dInfUnion
  congr 1
  funext x
  rw [abs_sub_comm]

/-- **Proposition 5.2.3** (reflexivity, union form). -/
theorem dInfUnion_self (f : ScalarProfile α) : dInfUnion f f = 0 := by
  unfold dInfUnion
  apply le_antisymm _ (zero_le _)
  apply iSup_le
  intro _
  simp [sub_self]

/-- The union distance is bounded above by 1, since profile values lie
    in [0, 1] and so do their differences in absolute value. -/
theorem dInfUnion_le_one (f g : ScalarProfile α) : dInfUnion f g ≤ 1 := by
  unfold dInfUnion
  apply iSup_le
  intro x
  have h_abs := f.abs_sub_zeroExtend_le_one g x
  calc ENNReal.ofReal |f.zeroExtend x - g.zeroExtend x|
      ≤ ENNReal.ofReal 1 := ENNReal.ofReal_le_ofReal h_abs
    _ = 1 := ENNReal.ofReal_one

/-- **Proposition 5.2bis.2** (triangle inequality, union form).

    The triangle inequality holds unconditionally for the union form.
    The proof applies the pointwise triangle inequality for `|·|`,
    distributes `ENNReal.ofReal` over the resulting sum, and uses the
    standard fact that the supremum of a pointwise sum is bounded by
    the sum of suprema. -/
theorem dInfUnion_triangle (f g h : ScalarProfile α) :
    dInfUnion f h ≤ dInfUnion f g + dInfUnion g h := by
  unfold dInfUnion
  apply iSup_le
  intro x
  have triangle_pt : |f.zeroExtend x - h.zeroExtend x|
      ≤ |f.zeroExtend x - g.zeroExtend x| + |g.zeroExtend x - h.zeroExtend x| := by
    have h_rewrite : (f.zeroExtend x - h.zeroExtend x) =
        (f.zeroExtend x - g.zeroExtend x) + (g.zeroExtend x - h.zeroExtend x) := by ring
    rw [h_rewrite]
    exact abs_add _ _
  calc ENNReal.ofReal |f.zeroExtend x - h.zeroExtend x|
      ≤ ENNReal.ofReal (|f.zeroExtend x - g.zeroExtend x| +
                        |g.zeroExtend x - h.zeroExtend x|) :=
        ENNReal.ofReal_le_ofReal triangle_pt
    _ = ENNReal.ofReal |f.zeroExtend x - g.zeroExtend x| +
        ENNReal.ofReal |g.zeroExtend x - h.zeroExtend x| :=
        ENNReal.ofReal_add (abs_nonneg _) (abs_nonneg _)
    _ ≤ (⨆ y : α, ENNReal.ofReal |f.zeroExtend y - g.zeroExtend y|) +
        (⨆ y : α, ENNReal.ofReal |g.zeroExtend y - h.zeroExtend y|) :=
        add_le_add 
          (le_iSup (fun y : α => ENNReal.ofReal |f.zeroExtend y - g.zeroExtend y|) x)
          (le_iSup (fun y : α => ENNReal.ofReal |g.zeroExtend y - h.zeroExtend y|) x)

/-! ## The shared form distance via intersection -/

/-- **Definition 5.1.1**: the $L^\infty$ shared distance.

    For two profiles `f, g`, the shared distance is the supremum of
    pointwise differences over the shared subdomain `f.domain ∩ g.domain`,
    with the convention `⊤` (i.e. `+∞`) when the intersection is empty.

    Reference: profile_comparison_v0_2.md §5.1.1. -/
noncomputable def dInfShared (f g : ScalarProfile α) : ℝ≥0∞ :=
  if (f.domain ∩ g.domain).Nonempty then
    ⨆ x ∈ f.domain ∩ g.domain, ENNReal.ofReal |f.zeroExtend x - g.zeroExtend x|
  else ⊤

/-! ### Basic properties of the shared form -/

/-- **Proposition 5.2.1** (non-negativity, shared form). -/
theorem dInfShared_nonneg (f g : ScalarProfile α) : 0 ≤ dInfShared f g :=
  bot_le

/-- **Proposition 5.2.2** (symmetry, shared form).

    Symmetry uses the commutativity of `Set.inter` to align the shared
    subdomains and `abs_sub_comm` to flip the pointwise absolute value. -/
theorem dInfShared_symm (f g : ScalarProfile α) :
    dInfShared f g = dInfShared g f := by
  unfold dInfShared
  by_cases h : (f.domain ∩ g.domain).Nonempty
  · have h' : (g.domain ∩ f.domain).Nonempty := by
      rw [Set.inter_comm]; exact h
    rw [if_pos h, if_pos h', Set.inter_comm]
    apply iSup_congr
    intro x
    apply iSup_congr
    intro _
    rw [abs_sub_comm]
  · have h' : ¬ (g.domain ∩ f.domain).Nonempty := by
      rw [Set.inter_comm]; exact h
    rw [if_neg h, if_neg h']

/-- **Proposition 5.2.3** (reflexivity, shared form).

    `dInfShared f f = 0` whenever `f.domain` is non-empty.

    If `f.domain` is empty, the convention gives `⊤`, which is not zero;
    this corresponds to the paper's convention that comparing profiles
    with no shared subdomain returns `+∞`. -/
theorem dInfShared_self_of_nonempty
    (f : ScalarProfile α) (h : f.domain.Nonempty) : dInfShared f f = 0 := by
  unfold dInfShared
  rw [Set.inter_self]
  rw [if_pos h]
  apply ENNReal.iSup_eq_zero.mpr
  intro x
  apply ENNReal.iSup_eq_zero.mpr
  intro _
  simp [sub_self]

/-- The shared distance is bounded above by 1 whenever the intersection
    is non-empty. -/
theorem dInfShared_le_one_of_nonempty (f g : ScalarProfile α)
    (h : (f.domain ∩ g.domain).Nonempty) : dInfShared f g ≤ 1 := by
  unfold dInfShared
  rw [if_pos h]
  apply iSup_le
  intro x
  apply iSup_le
  intro _
  have h_abs := f.abs_sub_zeroExtend_le_one g x
  calc ENNReal.ofReal |f.zeroExtend x - g.zeroExtend x|
      ≤ ENNReal.ofReal 1 := ENNReal.ofReal_le_ofReal h_abs
    _ = 1 := ENNReal.ofReal_one

/-- The shared distance is `⊤` exactly when the shared subdomain is empty. -/
theorem dInfShared_top_iff (f g : ScalarProfile α) :
    dInfShared f g = ⊤ ↔ ¬ (f.domain ∩ g.domain).Nonempty := by
  unfold dInfShared
  constructor
  · intro h
    by_contra h_ne
    rw [if_pos h_ne] at h
    have h_bound := dInfShared_le_one_of_nonempty f g h_ne
    unfold dInfShared at h_bound
    rw [if_pos h_ne] at h_bound
    rw [h] at h_bound
    exact absurd h_bound (by norm_num : ¬ (⊤ : ℝ≥0∞) ≤ 1)
  · intro h
    rw [if_neg h]

/-- **Proposition 5.2.6** (qualified triangle inequality, bridge form).

    If every point in the `f`/`h` shared domain also lies in `g.domain`, then
    `g` can mediate the pointwise triangle comparison on the whole domain used
    by `dInfShared f h`. -/
theorem dInfShared_triangle_of_bridge
    (f g h : ScalarProfile α)
    (hfh : (f.domain ∩ h.domain).Nonempty)
    (hbridge : f.domain ∩ h.domain ⊆ g.domain) :
    dInfShared f h ≤ dInfShared f g + dInfShared g h := by
  unfold dInfShared
  have hfg : (f.domain ∩ g.domain).Nonempty := by
    rcases hfh with ⟨x, hx⟩
    exact ⟨x, ⟨hx.1, hbridge hx⟩⟩
  have hgh : (g.domain ∩ h.domain).Nonempty := by
    rcases hfh with ⟨x, hx⟩
    exact ⟨x, ⟨hbridge hx, hx.2⟩⟩
  rw [if_pos hfh, if_pos hfg, if_pos hgh]
  apply iSup_le
  intro x
  apply iSup_le
  intro hx
  have hxg : x ∈ g.domain := hbridge hx
  have hxfg : x ∈ f.domain ∩ g.domain := ⟨hx.1, hxg⟩
  have hxgh : x ∈ g.domain ∩ h.domain := ⟨hxg, hx.2⟩
  have left_le :
      ENNReal.ofReal |f.zeroExtend x - g.zeroExtend x| ≤
        (⨆ y : α, ⨆ _ : y ∈ f.domain ∩ g.domain,
          ENNReal.ofReal |f.zeroExtend y - g.zeroExtend y|) := by
    exact le_trans
      (le_iSup
        (fun _ : x ∈ f.domain ∩ g.domain =>
          ENNReal.ofReal |f.zeroExtend x - g.zeroExtend x|) hxfg)
      (le_iSup
        (fun y : α => ⨆ _ : y ∈ f.domain ∩ g.domain,
          ENNReal.ofReal |f.zeroExtend y - g.zeroExtend y|) x)
  have right_le :
      ENNReal.ofReal |g.zeroExtend x - h.zeroExtend x| ≤
        (⨆ y : α, ⨆ _ : y ∈ g.domain ∩ h.domain,
          ENNReal.ofReal |g.zeroExtend y - h.zeroExtend y|) := by
    exact le_trans
      (le_iSup
        (fun _ : x ∈ g.domain ∩ h.domain =>
          ENNReal.ofReal |g.zeroExtend x - h.zeroExtend x|) hxgh)
      (le_iSup
        (fun y : α => ⨆ _ : y ∈ g.domain ∩ h.domain,
          ENNReal.ofReal |g.zeroExtend y - h.zeroExtend y|) x)
  have triangle_pt : |f.zeroExtend x - h.zeroExtend x|
      ≤ |f.zeroExtend x - g.zeroExtend x| + |g.zeroExtend x - h.zeroExtend x| := by
    have h_rewrite : (f.zeroExtend x - h.zeroExtend x) =
        (f.zeroExtend x - g.zeroExtend x) + (g.zeroExtend x - h.zeroExtend x) := by ring
    rw [h_rewrite]
    exact abs_add _ _
  calc ENNReal.ofReal |f.zeroExtend x - h.zeroExtend x|
      ≤ ENNReal.ofReal (|f.zeroExtend x - g.zeroExtend x| +
                        |g.zeroExtend x - h.zeroExtend x|) :=
        ENNReal.ofReal_le_ofReal triangle_pt
    _ = ENNReal.ofReal |f.zeroExtend x - g.zeroExtend x| +
        ENNReal.ofReal |g.zeroExtend x - h.zeroExtend x| :=
        ENNReal.ofReal_add (abs_nonneg _) (abs_nonneg _)
    _ ≤ (⨆ y : α, ⨆ _ : y ∈ f.domain ∩ g.domain,
          ENNReal.ofReal |f.zeroExtend y - g.zeroExtend y|) +
        (⨆ y : α, ⨆ _ : y ∈ g.domain ∩ h.domain,
          ENNReal.ofReal |g.zeroExtend y - h.zeroExtend y|) :=
        add_le_add left_le right_le

/-! ### The bounded-domain bound for the shared form

When the shared subdomain is non-empty, `dInfShared` is the supremum of
pointwise differences, bounded by 1 (above) and 0 (below). The bound
mirrors `dInfUnion_le_one`. -/

/-- The shared form is bounded above by 1 unconditionally, with `⊤` as the
    natural extension when the intersection is empty (`⊤ ≤ ⊤` is true). -/
theorem dInfShared_le_one_or_top (f g : ScalarProfile α) :
    dInfShared f g ≤ 1 ∨ dInfShared f g = ⊤ := by
  by_cases h : (f.domain ∩ g.domain).Nonempty
  · left; exact dInfShared_le_one_of_nonempty f g h
  · right; rw [dInfShared_top_iff]; exact h

end TLICA.ProfileComparison.Pointwise
