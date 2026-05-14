/-
TLICA.Profile — The base identity-correlation profile.

This module encodes the base profile $P^\rho_{m,t}$ of Definition 4.1.1 in the
v0.3.1 rigorous edition as a Lean structure. The profile is a function from a
domain (subset of a universal content-domain type α) to the closed unit
interval [0, 1], bundled with the proofs of non-negativity and ≤1 bounds.

A profile's `domain` is a `Set α` — the asymptotic content domain $A^m_t$
at some implicit $(m, t)$. Different profiles can have different domains;
profile comparison (in `TLICA.ProfileComparison.Pointwise`) operates on
pairs of profiles with possibly different domains in the same universal
content type.

The zero-extension `zeroExtend` lifts a profile to a function on the full
universal domain α, with value 0 outside the profile's domain. This is the
operational device that makes the union-form distance well-typed.

Reference: v0.3.1 rigorous edition,
  - 04_profiles.md §4.1.1 (base ρ-profile definition).
  - profile_comparison_v0_2.md §4 (notation), §5.1.1 (definition with
    foundation signature).
-/

import Mathlib.Algebra.Order.Field.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Data.Set.Basic
import Mathlib.Tactic.Linarith

namespace TLICA.Profile

open Classical

/-- A scalar identity-correlation profile on a universal content-domain
    type `α`.

    The profile carries its own `domain : Set α` (the asymptotic content
    domain at the implicit modeling I and time), the value function
    `toFun : ↥domain → ℝ`, and the [0, 1]-bound proofs.

    Reference: v0.3.1 rigorous edition, 04_profiles.md §4.1.1. -/
structure ScalarProfile (α : Type*) where
  /-- The asymptotic content domain `A^m_t` of this profile. -/
  domain : Set α
  /-- The profile value function on the domain. -/
  toFun : ↥domain → ℝ
  /-- Profile values are non-negative. -/
  toFun_nonneg : ∀ x : ↥domain, 0 ≤ toFun x
  /-- Profile values are at most 1. -/
  toFun_le_one : ∀ x : ↥domain, toFun x ≤ 1

namespace ScalarProfile

variable {α : Type*}

/-- The zero-extension of a profile to the universal domain.

    For `x ∈ f.domain`, `f.zeroExtend x = f.toFun ⟨x, h⟩` (the actual
    profile value). For `x ∉ f.domain`, `f.zeroExtend x = 0`.

    Reference: v0.3.1 rigorous edition, profile_comparison_v0_2.md §5.2bis.1
    (definition of zero-extension for the union-form distance). -/
noncomputable def zeroExtend (f : ScalarProfile α) : α → ℝ :=
  fun x => if h : x ∈ f.domain then f.toFun ⟨x, h⟩ else 0

theorem zeroExtend_of_mem (f : ScalarProfile α) (x : α) (h : x ∈ f.domain) :
    f.zeroExtend x = f.toFun ⟨x, h⟩ := by
  unfold zeroExtend
  rw [dif_pos h]

theorem zeroExtend_of_not_mem (f : ScalarProfile α) (x : α) (h : x ∉ f.domain) :
    f.zeroExtend x = 0 := by
  unfold zeroExtend
  rw [dif_neg h]

theorem zeroExtend_nonneg (f : ScalarProfile α) (x : α) : 0 ≤ f.zeroExtend x := by
  unfold zeroExtend
  split_ifs with h
  · exact f.toFun_nonneg ⟨x, h⟩
  · exact le_refl 0

theorem zeroExtend_le_one (f : ScalarProfile α) (x : α) : f.zeroExtend x ≤ 1 := by
  unfold zeroExtend
  split_ifs with h
  · exact f.toFun_le_one ⟨x, h⟩
  · linarith

theorem abs_sub_zeroExtend_le_one (f g : ScalarProfile α) (x : α) :
    |f.zeroExtend x - g.zeroExtend x| ≤ 1 := by
  have h1 : 0 ≤ f.zeroExtend x := f.zeroExtend_nonneg x
  have h2 : f.zeroExtend x ≤ 1 := f.zeroExtend_le_one x
  have h3 : 0 ≤ g.zeroExtend x := g.zeroExtend_nonneg x
  have h4 : g.zeroExtend x ≤ 1 := g.zeroExtend_le_one x
  rw [abs_le]
  constructor <;> linarith

end ScalarProfile

end TLICA.Profile
