/-
TLICA.PhiCoordinate — The truth-indistinguishability coordinate φ.

This module encodes the v0.3.1 rigorous edition's treatment of the
φ-coordinate, including the two named axioms (φ-admissibility and Tier-3
strictness) and the cogito-uniqueness theorem at the φ level
(Proposition 3.3.7).

The substantive content: φ takes value `1 - δ` exactly at the cogito and
strictly less than `1 - δ` at every non-cogito Tier-3 verified content.
The strict gap between the cogito and Tier-3 contents is the load-bearing
fact that licenses the architecture's three-tier ontology at the φ level
and that closes open question `oq:phi-tier-boundary`.

Reference: v0.3.1 rigorous edition,
  - 00_signature.md §0.14 (Axiom (φ admissibility), Axiom (Tier-3 strictness))
  - 03_coordinates.md §3.3 (the φ formula)
  - 03_coordinates.md §3.3.6 (Proposition 3.3.7)
  - sources/core/3_formal_apparatus.md line 181 (core admissibility bound).
-/

import TLICA.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum

namespace TLICA.PhiCoordinate

open KField

variable {K : Type*} [KField K]

/-- The φ-value of the cogito, fixed by the cogito φ-axiom.

    Reference: v0.3.1 rigorous edition, 00_signature.md §0.6
    (Axiom: φ(cogito, t) = 1 - δ). -/
def phiCogito : K := 1 - δ

/-- The φ-formula for a Tier-3 verified content with conditional depth `n`
    and empirical-robustness deficit `ε`.

    Reference: v0.3.1 rigorous edition, 03_coordinates.md §3.3.3
    (Tier-3 formula: φ(x) = 1 - n·δ - ε). -/
def phiTier3 (n : ℕ) (ε : K) : K := 1 - (n : K) * δ - ε

/-- The φ-admissibility axiom (as a proposition on `(n, ε)`).

    `ε + n·δ ≤ 1` for every verified content. This ensures
    `phiTier3 n ε ≥ 0` (lower bound on the Tier-3 formula).

    Reference: v0.3.1 rigorous edition, 00_signature.md §0.14
    (Axiom (φ admissibility), lines 143-149). Imported from
    sources/core/3_formal_apparatus.md line 181. -/
def PhiAdmissibility (n : ℕ) (ε : K) : Prop :=
  ε + (n : K) * δ ≤ 1

/-- The Tier-3 strictness axiom (as a proposition on `(n, ε)`).

    `n·δ + ε > δ` for every non-cogito Tier-3 verified content. This is
    the substantive postulate that ensures the cogito is the *unique*
    supremum of φ (rather than merely an upper bound).

    Reference: v0.3.1 rigorous edition, 00_signature.md §0.14
    (Axiom (Tier-3 strictness), lines 151-157). -/
def Tier3Strictness (n : ℕ) (ε : K) : Prop :=
  (n : K) * δ + ε > δ

/-- **Lower bound on φ for Tier-3 verified content**.

    Under the φ-admissibility axiom, `phiTier3 n ε ≥ 0`. This is the lower
    half of the range claim `phiTier3 n ε ∈ [0, 1 - δ]`.

    Reference: v0.3.1 rigorous edition, 03_coordinates.md §3.3.6 (a),
    first sentence. -/
theorem phi_tier3_nonneg
    (n : ℕ) (ε : K)
    (h_admiss : PhiAdmissibility n ε) :
    0 ≤ phiTier3 n ε := by
  unfold phiTier3 PhiAdmissibility at *
  linarith

/-- **Non-strict upper bound on φ for Tier-3 verified content**.

    For `n ≥ 1` and `ε ≥ 0`, `phiTier3 n ε ≤ phiCogito = 1 - δ`. This is
    the non-strict version of the cogito-supremum claim; admissibility is
    not used here, only `n ≥ 1` (conditional depth is at least 1 for
    Tier-3) and `ε ≥ 0` (deficit is non-negative).

    Reference: v0.3.1 rigorous edition, 03_coordinates.md §3.3.6 (a),
    last clause. -/
theorem phi_tier3_le_phiCogito
    (n : ℕ) (ε : K)
    (hn : 1 ≤ n) (hε : 0 ≤ ε) :
    phiTier3 n ε ≤ phiCogito := by
  unfold phiTier3 phiCogito
  have hδ : (0 : K) < δ := δ_pos
  have hn_cast : (1 : K) ≤ (n : K) := by exact_mod_cast hn
  have h_mul : δ ≤ (n : K) * δ := by
    have : (1 : K) * δ ≤ (n : K) * δ :=
      mul_le_mul_of_nonneg_right hn_cast (le_of_lt hδ)
    rwa [one_mul] at this
  linarith

/-- **Proposition 3.3.7** (strict form; principal cogito-uniqueness theorem at φ).

    Under the Tier-3 strictness axiom, every non-cogito Tier-3 verified
    content has `phiTier3 n ε < phiCogito = 1 - δ` strictly. Combined with
    `phiCogito = 1 - δ` (definitional), this establishes the cogito as
    the unique supremum of φ over its domain.

    The proof reduces to a single application of `linarith` after
    unfolding, because the strictness axiom literally is the inequality
    `δ < n·δ + ε`, which is equivalent to the goal `1 - n·δ - ε < 1 - δ`.

    Reference: v0.3.1 rigorous edition, 03_coordinates.md §3.3.6
    (Proposition 3.3.7), lines 92-102. -/
theorem phi_tier3_lt_phiCogito
    (n : ℕ) (ε : K)
    (h_strict : Tier3Strictness n ε) :
    phiTier3 n ε < phiCogito := by
  unfold phiTier3 phiCogito Tier3Strictness at *
  linarith

/-- **Proposition 3.3.7** (combined cogito-uniqueness statement).

    Together: at the cogito, `phiCogito = 1 - δ`; at every non-cogito
    Tier-3 verified content, `phiTier3 n ε < 1 - δ` strictly. The cogito
    is therefore the unique value at which φ attains `1 - δ`. -/
theorem cogito_unique_phi_supremum
    (n : ℕ) (ε : K)
    (h_strict : Tier3Strictness n ε) :
    phiTier3 n ε < (phiCogito : K) ∧ (phiCogito : K) = 1 - δ := by
  refine ⟨phi_tier3_lt_phiCogito n ε h_strict, rfl⟩

/-- **Admissible φ-domain** `D_φ` introduced in the v0.3.1 repair of
    Theorem 6.5.1.

    `D_φ = {α ∈ K : 0 ≤ α < 1 - δ}`. This is the set of φ-values attainable
    by non-cogito Tier-3 verified contents. In a non-Archimedean field,
    `D_φ` strictly contains the v0.2/v0.3 notation `(1 - δ - ℝ_{≥0})`,
    which is the defect that v0.3.1 corrects.

    Reference: v0.3.1 rigorous edition, 06_independence_lemmas.md §6.5
    (notational prelude to Theorem 6.5.1). -/
def DPhi (K : Type*) [KField K] : Set K :=
  {α : K | 0 ≤ α ∧ α < 1 - δ}

/-- The witnessing scenario of Proposition 6.3.1 produces a φ-value of the
    form `1 - 2·δ - e` for real `e ≥ 0` satisfying `2·δ + e ≤ 1`. We
    confirm here that such a value lies in `D_φ` whenever `0 ≤ e < 1 - 2·δ`.

    This lemma is referenced by `TLICA.NonReducibility`. -/
theorem two_delta_minus_real_in_DPhi
    (e : K) (he_nonneg : 0 ≤ e) (he_lt : e < 1 - 2 * δ) :
    (1 - 2 * δ - e) ∈ DPhi K := by
  unfold DPhi
  refine ⟨?_, ?_⟩
  · -- 0 ≤ 1 - 2δ - e
    linarith
  · -- 1 - 2δ - e < 1 - δ
    -- equivalent to 0 < δ + e, which follows from δ_pos and e ≥ 0
    have hδ : (0 : K) < δ := δ_pos
    linarith

end TLICA.PhiCoordinate
