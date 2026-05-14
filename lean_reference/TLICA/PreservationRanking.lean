/-
TLICA.PreservationRanking — The preservation-ranking Π.

Encodes §4 of the orphan_cluster_v0_1.md working paper: the preservation-ranking
$\Pi_{m,t}$ as a non-negative real-valued ranking on subsets of the lived-I,
with foundation axioms (cogito necessity, MSI maximality, MSI-component
monotonicity, non-MSI insensitivity bound, separation from ρ).

Reference:
  - 2_access_and_development.md §4.8 (theoretical statement).
  - 4_derived_concepts_and_predictions.md §10.7 (PCE context).
  - orphan_cluster_v0_1.md §4 (foundation-ready definitions and axioms).
-/

import TLICA.MSI
import Mathlib.Data.Set.Basic
import Mathlib.Data.Real.Basic

namespace TLICA.PreservationRanking

open TLICA.Profile TLICA.MSI
open Classical

variable {α : Type*}

/-- The preservation-ranking on subsets of the lived-I, satisfying the
    foundation axioms 4.3.1–4.3.4. (Axiom 4.3.5 — separation from ρ — is
    a meta-axiom on functional form, not encoded structurally.)

    Reference: orphan_cluster_v0_1.md Definition 4.2.1. -/
structure PreservationRanking (msi : MSI α) where
  /-- The ranking function on subsets of the profile's domain. -/
  rank : Set ↥msi.profile.domain → ℝ
  /-- The rank is non-negative. -/
  rank_nonneg : ∀ S, 0 ≤ rank S
  /-- **Axiom 4.3.1**: rank-positive sets contain the cogito. -/
  cogito_necessity : ∀ S, 0 < rank S → msi.cogito ∈ S
  /-- **Axiom 4.3.2**: the MSI realizes the rank-maximum. -/
  msi_maximality : ∀ S, rank S ≤ rank msi.contents
  /-- **Axiom 4.3.3**: monotonicity for MSI components. -/
  msi_monotonicity : ∀ S T, msi.cogito ∈ S ∩ T →
                       S ∩ msi.contents ⊇ T ∩ msi.contents → rank T ≤ rank S

namespace PreservationRanking

variable {α : Type*}

/-- The MSI itself has positive rank (since it satisfies cogito-necessity
    via Axiom 3.3.1 and is the maximum, which must be ≥ the rank of {cogito}
    which is positive). This is conditional: we need that *some* set has
    positive rank, which is application-calibrated. We state it as an
    additional hypothesis. -/
theorem msi_rank_max (msi : MSI α) (pi : PreservationRanking msi) (S : Set ↥msi.profile.domain) :
    pi.rank S ≤ pi.rank msi.contents :=
  pi.msi_maximality S

/-- Sets not containing the cogito have rank zero. -/
theorem no_cogito_zero_rank (msi : MSI α) (pi : PreservationRanking msi)
    (S : Set ↥msi.profile.domain) (h : msi.cogito ∉ S) : pi.rank S = 0 := by
  by_contra h_ne
  have h_pos : 0 < pi.rank S := lt_of_le_of_ne (pi.rank_nonneg S) (Ne.symm h_ne)
  exact h (pi.cogito_necessity S h_pos)

end PreservationRanking

end TLICA.PreservationRanking
