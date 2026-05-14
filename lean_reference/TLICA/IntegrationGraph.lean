/-
TLICA.IntegrationGraph — Integration graph lemmas.

This module currently contains the strict-ρ-bound lemma (Lemma 2.4.2 in
the v0.3.1 rigorous edition), which is the warm-up target for the
proof-assistant encoding phase. The lemma states that the normalization
function ρ = C/(1+C) is strictly bounded above by 1 for any non-negative
finite max-flow value C. Combined with the cogito's anchoring axiom
ρ(cogito) = 1, this strict bound is the load-bearing analytic fact behind
the architecture's commitment that the cogito uniquely attains ρ = 1.

Reference: v0.3.1 rigorous edition,
  - 02_graph_theory.md §2.4 (Lemma 2.4.2, strict bound for ρ off the cogito).
-/

import Mathlib.Algebra.Order.Field.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Data.Real.Basic

namespace TLICA.IntegrationGraph

/-- **Lemma 2.4.2** (strict ρ-bound, warm-up form).

    For every non-negative real `C` (interpreted as a finite max-flow value),
    the normalization `C / (1 + C)` is strictly less than `1`.

    This formulation uses ℝ since max-flow values in the apparatus are
    real-valued. The result lifts to any linear ordered field via
    `strict_quotient_bound_field` below.

    Reference: v0.3.1 rigorous edition, 02_graph_theory.md §2.4
    (Lemma 2.4.2). -/
theorem strict_rho_bound (C : ℝ) (hC : 0 ≤ C) : C / (1 + C) < 1 := by
  have h_pos : (0 : ℝ) < 1 + C := by linarith
  rw [div_lt_one h_pos]
  linarith

/-- **Lemma 2.4.2** (field-generic form).

    The strict bound `C / (1 + C) < 1` holds in any linear ordered field
    for any non-negative `C`. Useful when the bound is needed for K-valued
    quantities after embedding via the canonical map ℝ → K.

    Reference: v0.3.1 rigorous edition, 02_graph_theory.md §2.4. -/
theorem strict_quotient_bound_field {F : Type*} [LinearOrderedField F]
    (C : F) (hC : 0 ≤ C) : C / (1 + C) < 1 := by
  have h_pos : (0 : F) < 1 + C := by linarith
  rw [div_lt_one h_pos]
  linarith

/-- **Lemma 2.4.2** (range corollary).

    The same hypothesis gives `0 ≤ C / (1 + C)`, completing the
    range claim `C / (1 + C) ∈ [0, 1)`. -/
theorem rho_nonneg {F : Type*} [LinearOrderedField F]
    (C : F) (hC : 0 ≤ C) : 0 ≤ C / (1 + C) := by
  have h_pos : (0 : F) < 1 + C := by linarith
  exact div_nonneg hC (le_of_lt h_pos)

end TLICA.IntegrationGraph
