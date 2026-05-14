/-
TLICA.NonReducibility — Theorem 6.5.1.

This module encodes the formal-non-reducibility theorem of the v0.3.1
rigorous edition, after the `D_φ` repair. The theorem states that no
universal function `F` can recover any one of the three coordinates
from the other two, across all admissible model instances.

The proof strategy is by finite witness models. Each of the three
sub-claims is established by exhibiting two coordinate triples
`(ρ, φ, κ)` that agree on two coordinates and differ on the third.
Any putative universal function would have to take two different values
at the same input, contradicting its functionhood.

The proof here does not formalize the entire apparatus (modeling I's,
time, integration graphs, etc.). Instead, it formalizes only the
coordinate-triple-level content sufficient for the non-reducibility
argument. The witness constructions correspond directly to those of
Propositions 6.2.1, 6.3.1, and 6.4.1 in the rigorous edition, projected
to their coordinate triples.

Reference: v0.3.1 rigorous edition,
  - 06_independence_lemmas.md §6.2-6.4 (the three witnessing propositions)
  - 06_independence_lemmas.md §6.5 (Theorem 6.5.1, with the v0.3.1 D_φ repair).
-/

import TLICA.PhiCoordinate
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum

namespace TLICA.NonReducibility

open KField TLICA.PhiCoordinate

variable {K : Type*} [KField K]

/-- A coordinate triple `(ρ, φ, κ)` produced by some admissible model
    instance at some `(t, x)`.

    `ρ ∈ [0, 1]`, `κ ∈ [0, 1]`, `φ ∈ D_φ = {α ∈ K : 0 ≤ α < 1 - δ}`.

    Reference: v0.3.1 rigorous edition, 06_independence_lemmas.md §6.5
    (notational prelude). -/
structure CoordinateTriple (K : Type*) [KField K] where
  ρ : ℝ
  φ : K
  κ : ℝ
  ρ_nonneg : 0 ≤ ρ
  ρ_le_one : ρ ≤ 1
  φ_in_DPhi : φ ∈ DPhi K
  κ_nonneg : 0 ≤ κ
  κ_le_one : κ ≤ 1

/-- **Witness for Proposition 6.2.1** (non-reducibility of ρ from (φ, κ)).

    Two coordinate triples agreeing on `(φ, κ)` and differing on `ρ`.

    The witness uses `φ = 1 - δ - 1/2` (a length-1 pathway with ε = 1/2)
    and `κ = 1/2` for both triples, and `ρ = 1/2` vs `ρ = 1/11` to
    distinguish them. The construction parallels the integration-graph
    construction in Proposition 6.2.1: same source-contact and same
    verification length, differing only in the graph-theoretic max-flow.

    Reference: v0.3.1 rigorous edition, 06_independence_lemmas.md §6.2. -/
noncomputable def witness_rho_1 : CoordinateTriple K := {
  ρ := 1/2
  φ := 1 - δ - 1/2
  κ := 1/2
  ρ_nonneg := by norm_num
  ρ_le_one := by norm_num
  φ_in_DPhi := by
    unfold DPhi
    refine ⟨?_, ?_⟩
    · -- 0 ≤ 1 - δ - 1/2
      -- Requires δ ≤ 1/2, which follows from δ_lt_half.
      have h := δ_lt_half (K := K)
      linarith
    · -- 1 - δ - 1/2 < 1 - δ
      linarith
  κ_nonneg := by norm_num
  κ_le_one := by norm_num
}

/-- The second witness for Proposition 6.2.1: same `(φ, κ)` as `witness_rho_1`
    but `ρ = 1/11` instead of `1/2`. -/
noncomputable def witness_rho_2 : CoordinateTriple K := {
  ρ := 1/11
  φ := 1 - δ - 1/2
  κ := 1/2
  ρ_nonneg := by norm_num
  ρ_le_one := by norm_num
  φ_in_DPhi := by
    unfold DPhi
    refine ⟨?_, ?_⟩
    · have h := δ_lt_half (K := K)
      linarith
    · linarith
  κ_nonneg := by norm_num
  κ_le_one := by norm_num
}

/-- **Proposition 6.2.1** (formal): no function `F_ρ` of `(φ, κ)` recovers
    `ρ` across all admissible coordinate triples.

    Reference: v0.3.1 rigorous edition, 06_independence_lemmas.md §6.2. -/
theorem no_F_rho :
    ¬ ∃ F : K → ℝ → ℝ,
        ∀ (t : CoordinateTriple K), F t.φ t.κ = t.ρ := by
  rintro ⟨F, hF⟩
  -- Instantiate at both witnesses.
  have h1 := hF (witness_rho_1 (K := K))
  have h2 := hF (witness_rho_2 (K := K))
  -- The two witnesses have the same φ and κ, but different ρ.
  simp only [witness_rho_1, witness_rho_2] at h1 h2
  -- F (1 - δ - 1/2) (1/2) = 1/2 and = 1/11, contradiction.
  rw [h1] at h2
  norm_num at h2

/-- **Witness for Proposition 6.3.1** (non-reducibility of φ from (ρ, κ)).

    Two coordinate triples agreeing on `(ρ, κ)` and differing on `φ`.

    The first witness has `φ = 1 - δ - 1/2` (length-1 pathway, ε = 1/2),
    and the second has `φ = 1 - 2·δ - 1/2` (length-2 pathway, ε = 1/2).
    The φ-values differ by exactly δ, the architecture's infinitesimal.

    Reference: v0.3.1 rigorous edition, 06_independence_lemmas.md §6.3. -/
noncomputable def witness_phi_1 : CoordinateTriple K := {
  ρ := 1/2
  φ := 1 - δ - 1/2
  κ := 1/2
  ρ_nonneg := by norm_num
  ρ_le_one := by norm_num
  φ_in_DPhi := by
    unfold DPhi
    refine ⟨?_, ?_⟩
    · have h := δ_lt_half (K := K)
      linarith
    · linarith
  κ_nonneg := by norm_num
  κ_le_one := by norm_num
}

/-- Second witness for Proposition 6.3.1: `φ = 1 - 2·δ - 1/2`.

    Crucially, the φ-value `1 - 2·δ - 1/2` is in `D_φ` (i.e. `φ < 1 - δ`)
    iff `δ + 1/2 > 0`, which holds. This is the φ-value type that the
    v0.3.1 `D_φ` repair was designed to accommodate — it is *not* of the
    form `1 - δ - r` for any real `r`. -/
noncomputable def witness_phi_2 : CoordinateTriple K := {
  ρ := 1/2
  φ := 1 - 2 * δ - 1/2
  κ := 1/2
  ρ_nonneg := by norm_num
  ρ_le_one := by norm_num
  φ_in_DPhi := by
    -- φ = 1 - 2δ - 1/2 should be in D_φ.
    unfold DPhi
    refine ⟨?_, ?_⟩
    · -- 0 ≤ 1 - 2δ - 1/2: need δ < 1/4 (so 2δ < 1/2).
      -- δ_lt_rat (1/4) gives δ < 1/4.
      have h : δ < (((1/4 : ℚ) : K)) := δ_lt_rat (1/4) (by norm_num : (0 : ℚ) < 1/4)
      norm_num at h
      linarith
    · -- 1 - 2δ - 1/2 < 1 - δ ⟺ -δ - 1/2 < 0 ⟺ δ + 1/2 > 0.
      have h := δ_pos (K := K)
      linarith
  κ_nonneg := by norm_num
  κ_le_one := by norm_num
}

/-- **Proposition 6.3.1** (formal): no function `F_φ` of `(ρ, κ)` recovers
    `φ` across all admissible coordinate triples.

    The witnessing scenario relies on the v0.3.1 `D_φ` repair: the
    φ-value `1 - 2·δ - 1/2` of the second witness is in `D_φ` but is
    not of the form `1 - δ - r` for any real `r ≥ 0`. Theorem 6.5.1 as
    stated in v0.3 (with the inadequate notation) failed to range over
    such values; the v0.3.1 reformulation with `D_φ` is precisely what
    makes this witnessing scenario admissible. -/
theorem no_F_phi :
    ¬ ∃ F : ℝ → ℝ → K,
        ∀ (t : CoordinateTriple K), F t.ρ t.κ = t.φ := by
  rintro ⟨F, hF⟩
  have h1 := hF (witness_phi_1 (K := K))
  have h2 := hF (witness_phi_2 (K := K))
  simp only [witness_phi_1, witness_phi_2] at h1 h2
  -- F (1/2) (1/2) = 1 - δ - 1/2 and = 1 - 2δ - 1/2
  -- Contradiction: 1 - δ - 1/2 ≠ 1 - 2δ - 1/2 because δ ≠ 0.
  rw [h1] at h2
  -- h2 : 1 - δ - 1/2 = 1 - 2δ - 1/2
  have hδ : (0 : K) < δ := δ_pos
  linarith

/-- **Witness for Proposition 6.4.1** (non-reducibility of κ from (ρ, φ)).

    Two coordinate triples agreeing on `(ρ, φ)` and differing on `κ`.

    Both have `ρ = 1/2`, `φ = 1 - δ - 1/2`. The first has `κ = 1/3`, the
    second has `κ = 2/3`.

    Reference: v0.3.1 rigorous edition, 06_independence_lemmas.md §6.4. -/
noncomputable def witness_kappa_1 : CoordinateTriple K := {
  ρ := 1/2
  φ := 1 - δ - 1/2
  κ := 1/3
  ρ_nonneg := by norm_num
  ρ_le_one := by norm_num
  φ_in_DPhi := by
    unfold DPhi
    refine ⟨?_, ?_⟩
    · have h := δ_lt_half (K := K)
      linarith
    · linarith
  κ_nonneg := by norm_num
  κ_le_one := by norm_num
}

noncomputable def witness_kappa_2 : CoordinateTriple K := {
  ρ := 1/2
  φ := 1 - δ - 1/2
  κ := 2/3
  ρ_nonneg := by norm_num
  ρ_le_one := by norm_num
  φ_in_DPhi := by
    unfold DPhi
    refine ⟨?_, ?_⟩
    · have h := δ_lt_half (K := K)
      linarith
    · linarith
  κ_nonneg := by norm_num
  κ_le_one := by norm_num
}

/-- **Proposition 6.4.1** (formal): no function `F_κ` of `(ρ, φ)` recovers
    `κ` across all admissible coordinate triples. -/
theorem no_F_kappa :
    ¬ ∃ F : ℝ → K → ℝ,
        ∀ (t : CoordinateTriple K), F t.ρ t.φ = t.κ := by
  rintro ⟨F, hF⟩
  have h1 := hF (witness_kappa_1 (K := K))
  have h2 := hF (witness_kappa_2 (K := K))
  simp only [witness_kappa_1, witness_kappa_2] at h1 h2
  rw [h1] at h2
  norm_num at h2

/-- **Theorem 6.5.1** (formal non-reducibility of the three coordinates).

    The conjunction of the three non-reducibility propositions. None of the
    three coordinates can be recovered as a universal function of the other
    two across all admissible coordinate triples.

    Reference: v0.3.1 rigorous edition, 06_independence_lemmas.md §6.5. -/
theorem formal_non_reducibility :
    (¬ ∃ F : K → ℝ → ℝ, ∀ (t : CoordinateTriple K), F t.φ t.κ = t.ρ) ∧
    (¬ ∃ F : ℝ → ℝ → K, ∀ (t : CoordinateTriple K), F t.ρ t.κ = t.φ) ∧
    (¬ ∃ F : ℝ → K → ℝ, ∀ (t : CoordinateTriple K), F t.ρ t.φ = t.κ) :=
  ⟨no_F_rho, no_F_phi, no_F_kappa⟩

end TLICA.NonReducibility
