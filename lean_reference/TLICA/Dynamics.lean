/-
TLICA.Dynamics — Apparatus dynamics lemmas.

This module encodes Proposition 5.7.2 of the v0.3.1 rigorous edition:
uniform convergence of the mode aggregation under the Weierstrass M-test.

Substantive content: the per-mode functions `ρ_k : T → ℝ` are uniformly
bounded by `1` in absolute value, and the weights `(a_k)` are summable
and non-negative. Therefore the partial sums `∑ k ∈ s, a_k · ρ_k(t)`
converge uniformly in `t` (as `s → ⊤` in the directed set of finite
subsets of the mode index) to the limit `∑' k, a_k · ρ_k(t)`. The proof
applies mathlib's `tendstoUniformly_tsum` with majorant `M_k = a_k`.

Reference: v0.3.1 rigorous edition,
  - 05_dynamics.md §5.7 (Proposition 5.7.2).
-/

import TLICA.ModeAggregation
import Mathlib.Analysis.Normed.Module.Basic
import Mathlib.Analysis.NormedSpace.FunctionSeries
import Mathlib.Topology.UniformSpace.UniformConvergence
import Mathlib.Topology.UniformSpace.UniformConvergenceTopology
import Mathlib.Tactic.Linarith

namespace TLICA.Dynamics

open Filter

/-- **Proposition 5.7.2** (uniform convergence of the mode aggregation).

    Given a summable non-negative weighting `(a_k)` and a family of
    functions `ρ_k : T → ℝ` with `|ρ_k(t)| ≤ 1` for every `(k, t)`,
    the partial sums `∑ k ∈ s, a_k · ρ_k(t)` converge to `∑' k, a_k · ρ_k(t)`
    uniformly in `t` as `s` ranges over the directed set of finite
    subsets of the mode index `ι`.

    Proof by the Weierstrass M-test: the per-term bound is
    `‖a_k · ρ_k(t)‖ = a_k · |ρ_k(t)| ≤ a_k · 1 = a_k`, and `(a_k)` is
    summable by hypothesis, so the majorant condition of
    `tendstoUniformly_tsum` is satisfied.

    Reference: v0.3.1 rigorous edition, 05_dynamics.md §5.7
    (Proposition 5.7.2). -/
theorem mode_aggregation_uniform_convergent
    {ι T : Type*} (a : ι → ℝ) (ρ : ι → T → ℝ)
    (ha_nonneg : ∀ k, 0 ≤ a k)
    (ha_sum : Summable a)
    (hρ_bound : ∀ k t, |ρ k t| ≤ 1) :
    TendstoUniformly
      (fun (s : Finset ι) (t : T) => ∑ k ∈ s, a k * ρ k t)
      (fun t => ∑' k, a k * ρ k t)
      atTop := by
  apply tendstoUniformly_tsum ha_sum
  intro k t
  -- Goal after `tendstoUniformly_tsum`: ‖a k * ρ k t‖ ≤ a k.
  rw [Real.norm_eq_abs, abs_mul, abs_of_nonneg (ha_nonneg k)]
  -- Goal: a k * |ρ k t| ≤ a k.
  have h_bound : |ρ k t| ≤ 1 := hρ_bound k t
  have h_abs_nonneg : 0 ≤ |ρ k t| := abs_nonneg _
  nlinarith [ha_nonneg k, h_abs_nonneg]

end TLICA.Dynamics
