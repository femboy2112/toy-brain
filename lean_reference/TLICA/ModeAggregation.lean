/-
TLICA.ModeAggregation — Scalar mode aggregation.

This module encodes Proposition 2.5.1 of the v0.3.1 rigorous edition: the
scalar identity-correlation `ρ(x)` formed by weighting the per-mode
correlations `ρ_k(x)` by a summable probability weighting `(a_k)` is

  (i) absolutely convergent,
  (ii) bounded in [0, 1],
  (iii) strictly less than 1 for non-cogito x.

Reference: v0.3.1 rigorous edition,
  - 02_graph_theory.md §2.5 (Proposition 2.5.1, scalar aggregation).
-/

import TLICA.IntegrationGraph
import Mathlib.Analysis.Normed.Module.Basic
import Mathlib.Topology.Algebra.InfiniteSum.Basic
import Mathlib.Topology.Algebra.InfiniteSum.Order
import Mathlib.Topology.Instances.ENNReal
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity

namespace TLICA.ModeAggregation

/-- **Proposition 2.5.1 (i)**: absolute convergence of the weighted sum.

    Given a summable non-negative weighting `(a_k)` and per-mode values
    `ρ_k ∈ [0, 1]`, the term-wise product `(a_k · ρ_k)` is summable.

    The proof is by comparison: `0 ≤ a_k · ρ_k ≤ a_k`, and `(a_k)` is
    summable.

    Reference: v0.3.1 rigorous edition, 02_graph_theory.md §2.5 (i). -/
theorem mode_aggregation_summable
    {ι : Type*} (a : ι → ℝ) (ρ : ι → ℝ)
    (ha_nonneg : ∀ k, 0 ≤ a k)
    (ha_sum : Summable a)
    (hρ_bound : ∀ k, ρ k ≤ 1)
    (hρ_nonneg : ∀ k, 0 ≤ ρ k) :
    Summable (fun k => a k * ρ k) := by
  apply Summable.of_nonneg_of_le
    (fun k => mul_nonneg (ha_nonneg k) (hρ_nonneg k))
    (fun k => ?_)
    ha_sum
  -- Goal: a k * ρ k ≤ a k.
  have := hρ_bound k
  nlinarith [ha_nonneg k]

/-- **Proposition 2.5.1 (ii) lower bound**: the weighted sum is non-negative.

    Reference: v0.3.1 rigorous edition, 02_graph_theory.md §2.5 (ii). -/
theorem mode_aggregation_nonneg
    {ι : Type*} (a : ι → ℝ) (ρ : ι → ℝ)
    (ha_nonneg : ∀ k, 0 ≤ a k)
    (hρ_nonneg : ∀ k, 0 ≤ ρ k) :
    0 ≤ ∑' k, a k * ρ k := by
  apply tsum_nonneg
  intro k
  exact mul_nonneg (ha_nonneg k) (hρ_nonneg k)

/-- **Proposition 2.5.1 (ii) upper bound**: the weighted sum is at most 1.

    Given that the weights sum to 1 and the per-mode values are bounded by 1,
    the aggregation is bounded by `∑' k, a k = 1`.

    Reference: v0.3.1 rigorous edition, 02_graph_theory.md §2.5 (ii). -/
theorem mode_aggregation_le_one
    {ι : Type*} (a : ι → ℝ) (ρ : ι → ℝ)
    (ha_nonneg : ∀ k, 0 ≤ a k)
    (ha_sum : Summable a)
    (ha_total : ∑' k, a k = 1)
    (hρ_bound : ∀ k, ρ k ≤ 1)
    (hρ_nonneg : ∀ k, 0 ≤ ρ k) :
    ∑' k, a k * ρ k ≤ 1 := by
  calc ∑' k, a k * ρ k
      ≤ ∑' k, a k := by
        apply tsum_le_tsum
        · intro k
          have := hρ_bound k
          nlinarith [ha_nonneg k]
        · exact mode_aggregation_summable a ρ ha_nonneg ha_sum hρ_bound hρ_nonneg
        · exact ha_sum
    _ = 1 := ha_total

/-- **Proposition 2.5.1 (iii)**: strict bound for non-cogito x.

    If for some mode `k₀` we have `ρ k₀ < 1` strictly (the cogito's
    characteristic property fails), and `a k₀ > 0` strictly (mode `k₀` has
    nonzero weight), then the aggregation is strictly less than 1.

    The proof: split the aggregation as `a k₀ · ρ k₀ + ∑' k ≠ k₀, a k · ρ k`,
    bound the second sum by `∑' k ≠ k₀, a k = 1 - a k₀`, and use the strict
    inequality on the `k₀` term.

    Reference: v0.3.1 rigorous edition, 02_graph_theory.md §2.5 (iii). -/
theorem mode_aggregation_lt_one
    {ι : Type*} [DecidableEq ι]
    (a : ι → ℝ) (ρ : ι → ℝ)
    (ha_nonneg : ∀ k, 0 ≤ a k)
    (ha_sum : Summable a)
    (ha_total : ∑' k, a k = 1)
    (hρ_bound : ∀ k, ρ k ≤ 1)
    (hρ_nonneg : ∀ k, 0 ≤ ρ k)
    (k₀ : ι)
    (ha_k₀ : 0 < a k₀)
    (hρ_k₀ : ρ k₀ < 1) :
    ∑' k, a k * ρ k < 1 := by
  -- Strategy: bound `a k · ρ k ≤ a k` everywhere, with strict inequality at k₀.
  -- Then `∑' k, a k · ρ k ≤ ∑' k, a k = 1`, with the difference at k₀
  -- guaranteeing strict.
  have h_sum_prod : Summable (fun k => a k * ρ k) :=
    mode_aggregation_summable a ρ ha_nonneg ha_sum hρ_bound hρ_nonneg
  -- Define the gap function g k = a k - a k * ρ k = a k * (1 - ρ k) ≥ 0.
  have h_gap_nonneg : ∀ k, 0 ≤ a k - a k * ρ k := by
    intro k
    have h1 := ha_nonneg k
    have h2 := hρ_bound k
    nlinarith
  have h_gap_summable : Summable (fun k => a k - a k * ρ k) :=
    ha_sum.sub h_sum_prod
  have h_gap_k₀_pos : 0 < a k₀ - a k₀ * ρ k₀ := by
    have : a k₀ * (1 - ρ k₀) > 0 :=
      mul_pos ha_k₀ (by linarith : (0 : ℝ) < 1 - ρ k₀)
    linarith [this]
  -- The tsum of g is strictly positive:
  have h_gap_tsum_pos : 0 < ∑' k, (a k - a k * ρ k) := by
    apply tsum_pos h_gap_summable h_gap_nonneg k₀ h_gap_k₀_pos
  -- And tsum g = tsum a - tsum (a * ρ) = 1 - tsum (a * ρ).
  rw [tsum_sub ha_sum h_sum_prod, ha_total] at h_gap_tsum_pos
  linarith

end TLICA.ModeAggregation
