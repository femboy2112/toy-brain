/-
TLICA.Basic — The architecture's coefficient field K.

The coefficient field K of the TLICA apparatus is a linear ordered field
equipped with a designated positive infinitesimal δ ∈ (0, 1).

The non-Archimedean property — that δ is strictly less than every positive
rational — is needed for the typed-function statement of Theorem 6.5.1
(in particular, for the well-definedness of the admissible φ-domain
D_φ = {α ∈ K : 0 ≤ α < 1 - δ} as strictly containing the v0.2/v0.3
notation (1 - δ - ℝ_{≥0})).

The `KField` typeclass below encodes the minimum structure needed for the
proofs in this project. The non-Archimedean infinitesimal property
(`δ_lt_rat`) is included so that downstream witness constructions for
Theorem 6.5.1 can produce φ-values such as `1 - 2·δ - 1/2` and verify
that they fall in D_φ.

Reference: v0.3.1 rigorous edition,
  - 00_signature.md §0.3 (K-field requirements)
  - 00_signature.md §0.6 (cogito φ-axiom: φ(cogito) = 1 - δ)
  - 06_independence_lemmas.md §6.5 (Theorem 6.5.1, D_φ definition).
-/

import Mathlib.Algebra.Order.Field.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

namespace TLICA

/-- The architecture's coefficient field.

    `K` is a linear ordered field carrying a designated positive
    infinitesimal `δ ∈ (0, 1)`. The non-Archimedean property
    `δ < q` for every positive rational `q` ensures that `δ` cannot
    be cleared by any real-valued operation in the apparatus. -/
class KField (K : Type*) extends LinearOrderedField K where
  /-- The infinitesimal δ. -/
  δ : K
  /-- δ is strictly positive. -/
  δ_pos : (0 : K) < δ
  /-- δ is strictly below 1. -/
  δ_lt_one : δ < (1 : K)
  /-- δ is non-Archimedean: smaller than every positive rational. -/
  δ_lt_rat : ∀ q : ℚ, 0 < q → δ < (q : K)

namespace KField

variable {K : Type*} [KField K]

@[simp] lemma δ_nonneg : (0 : K) ≤ δ := le_of_lt δ_pos

@[simp] lemma one_sub_δ_pos : (0 : K) < 1 - δ := by
  have h : δ < (1 : K) := δ_lt_one
  linarith

@[simp] lemma one_sub_δ_lt_one : (1 : K) - δ < 1 := by
  have h : (0 : K) < δ := δ_pos
  linarith

lemma δ_lt_half : δ < (1/2 : K) := by
  have h : δ < (((1/2 : ℚ) : K)) := δ_lt_rat (1/2) (by norm_num : (0 : ℚ) < 1/2)
  norm_num at h
  exact h

end KField

end TLICA
