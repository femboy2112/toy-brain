/-
TLICA.ProfileComparison.ShellRefinement — Shell-stratified distance bounds.

This module encodes tractable shell-stratified distance bounds from Proposition
5.3.1 and Corollary 5.3.2 of the v0.2 profile-comparison working paper.

The strategy: prove the same-shell bound (`sameShellBound`) as the
load-bearing tractable case. The general `shellStratifiedBound` requires more
source-grounded boundary conventions for shell 0 (cogito) and shell 6 (outer),
so it is recorded as an explicit deferred target rather than as a theorem.
The downstream corollary `shellStableDistanceVanishing_simple` is derivable
from `sameShellBound` under the single-shell hypothesis.

Reference: v0.3.1 rigorous edition + profile_comparison_v0_2.md,
  - 04_profiles.md §4.3.1 (shell stratification).
  - profile_comparison_v0_2.md §5.3 (Proposition 5.3.1, Corollary 5.3.2).
-/

import TLICA.ProfileComparison.Pointwise
import Mathlib.Tactic.Linarith

namespace TLICA.ProfileComparison.ShellRefinement

open TLICA.Profile TLICA.ProfileComparison.Pointwise
open Classical

variable {α : Type*}

/-- A strictly-decreasing threshold sequence for the shell partition. -/
structure ShellThresholds where
  r : Fin 6 → ℝ
  r_zero : r 0 = 1
  r_five_pos : 0 < r 5
  r_strict_anti : StrictAnti r

namespace ShellThresholds

variable (rs : ShellThresholds)

/-- The maximal gap between adjacent thresholds across the partition. -/
noncomputable def maxGap : ℝ :=
  max (rs.r 0 - rs.r 1)
    (max (rs.r 1 - rs.r 2)
      (max (rs.r 2 - rs.r 3)
        (max (rs.r 3 - rs.r 4) (rs.r 4 - rs.r 5))))

/-- Every adjacent-threshold gap is positive. -/
theorem adjacent_gap_pos (i : Fin 5) :
    0 < rs.r ⟨i.val, by omega⟩ - rs.r ⟨i.val + 1, by omega⟩ := by
  have h : (⟨i.val, by omega⟩ : Fin 6) < ⟨i.val + 1, by omega⟩ := by
    simp [Fin.lt_iff_val_lt_val]
  have := rs.r_strict_anti h
  linarith

end ShellThresholds

/-- Membership in shell `i`, represented as the half-open interval
    `[r_(i+1), r_i)`.

    This covers the five interior shells determined directly by the six
    encoded thresholds. Boundary shells 0 and 6 from the prose source need
    additional conventions and are not included in this predicate. -/
def shellOf (rs : ShellThresholds) (i : Fin 5) (a : ℝ) : Prop :=
  rs.r ⟨i.val + 1, by omega⟩ ≤ a ∧ a < rs.r ⟨i.val, by omega⟩

/-- Absolute index distance between the five interior shell indices. -/
def interiorShellIndexDistance (i j : Fin 5) : Nat :=
  if i.val ≤ j.val then j.val - i.val else i.val - j.val

/-- Interior shell index distance vanishes on the diagonal. -/
theorem interiorShellIndexDistance_self (i : Fin 5) :
    interiorShellIndexDistance i i = 0 := by
  simp [interiorShellIndexDistance]

/-- Interior shell index distance is symmetric. -/
theorem interiorShellIndexDistance_symm (i j : Fin 5) :
    interiorShellIndexDistance i j = interiorShellIndexDistance j i := by
  unfold interiorShellIndexDistance
  split_ifs with hij hji <;> omega

/-- Seven shell indices from the source convention: cogito, five interior
    threshold shells, and the outer low-correlation shell. -/
inductive ShellIndex7 where
  | cogito
  | interior : Fin 5 → ShellIndex7
  | outer
  deriving DecidableEq

/-- Lower scalar endpoint for a source-level seven-shell index. -/
def shellLowerEndpoint (rs : ShellThresholds) : ShellIndex7 → ℝ
  | ShellIndex7.cogito => 1
  | ShellIndex7.interior i => rs.r ⟨i.val + 1, by omega⟩
  | ShellIndex7.outer => 0

/-- Upper scalar endpoint for a source-level seven-shell index. -/
def shellUpperEndpoint (rs : ShellThresholds) : ShellIndex7 → ℝ
  | ShellIndex7.cogito => 1
  | ShellIndex7.interior i => rs.r ⟨i.val, by omega⟩
  | ShellIndex7.outer => rs.r 5

/-- Endpoint-bound value used by the full seven-shell scalar estimate. -/
noncomputable def shellEndpointBound
    (rs : ShellThresholds) (i j : ShellIndex7) : ℝ :=
  max |shellUpperEndpoint rs i - shellLowerEndpoint rs j|
    |shellLowerEndpoint rs i - shellUpperEndpoint rs j|

/-- Boundary-aware scalar shell membership.

    This is additive over the existing interior `shellOf`. It records the
    source convention from Definition 4.3.1: shell 0 is the cogito singleton,
    shells 1-5 are the existing half-open threshold intervals, and shell 6 is
    the low-correlation interval `[0, r_5)`. -/
def shellOf7 (rs : ShellThresholds) : ShellIndex7 → ℝ → Prop
  | ShellIndex7.cogito, a => a = 1
  | ShellIndex7.interior i, a => shellOf rs i a
  | ShellIndex7.outer, a => 0 ≤ a ∧ a < rs.r 5

/-- Interior-shell members are nonnegative under the current threshold
    convention. -/
theorem shellOf_nonneg (rs : ShellThresholds) (i : Fin 5) (a : ℝ)
    (ha : shellOf rs i a) : 0 ≤ a := by
  have hpos : 0 < rs.r ⟨i.val + 1, by omega⟩ := by
    by_cases htop : i.val + 1 = 5
    · simpa [htop] using rs.r_five_pos
    · have hlt : (⟨i.val + 1, by omega⟩ : Fin 6) < 5 := by
        simp [Fin.lt_iff_val_lt_val]
        omega
      have hgt := rs.r_strict_anti hlt
      linarith [rs.r_five_pos]
  exact le_trans hpos.le ha.1

/-- Interior-shell members are bounded above by the normalized top threshold. -/
theorem shellOf_le_one (rs : ShellThresholds) (i : Fin 5) (a : ℝ)
    (ha : shellOf rs i a) : a ≤ 1 := by
  have hle : rs.r ⟨i.val, by omega⟩ ≤ 1 := by
    by_cases hzero : i.val = 0
    · have hfin : (⟨i.val, by omega⟩ : Fin 6) = 0 := by
        ext
        simp [hzero]
      rw [hfin, rs.r_zero]
    · have hpos : (0 : Fin 6) < ⟨i.val, by omega⟩ := by
        simp [Fin.lt_iff_val_lt_val]
        omega
      have hlt := rs.r_strict_anti hpos
      linarith [rs.r_zero]
  exact le_trans ha.2.le hle

/-- Seven-shell membership gives the lower endpoint bound. -/
theorem shellOf7_lower_le (rs : ShellThresholds) (s : ShellIndex7) (a : ℝ)
    (ha : shellOf7 rs s a) :
    shellLowerEndpoint rs s ≤ a := by
  cases s with
  | cogito =>
      simp [shellOf7] at ha
      subst a
      norm_num [shellLowerEndpoint]
  | interior i =>
      exact ha.1
  | outer =>
      exact ha.1

/-- Seven-shell membership gives the upper endpoint bound. -/
theorem shellOf7_le_upper (rs : ShellThresholds) (s : ShellIndex7) (a : ℝ)
    (ha : shellOf7 rs s a) :
    a ≤ shellUpperEndpoint rs s := by
  cases s with
  | cogito =>
      simp [shellOf7] at ha
      subst a
      norm_num [shellUpperEndpoint]
  | interior i =>
      exact ha.2.le
  | outer =>
      exact ha.2.le

/-- Every boundary-aware shell member lies in the normalized interval `[0, 1]`. -/
theorem shellOf7_mem_Icc_zero_one (rs : ShellThresholds) (s : ShellIndex7) (a : ℝ)
    (ha : shellOf7 rs s a) :
    0 ≤ a ∧ a ≤ 1 := by
  cases s with
  | cogito =>
      simp [shellOf7] at ha
      subst a
      norm_num
  | interior i =>
      exact ⟨shellOf_nonneg rs i a ha, shellOf_le_one rs i a ha⟩
  | outer =>
      have hlt : rs.r 5 < 1 := by
        have hstrict := rs.r_strict_anti (by decide : (0 : Fin 6) < 5)
        linarith [rs.r_zero]
      exact ⟨ha.1, le_trans ha.2.le hlt.le⟩

/-- Cogito-shell scalar members have value `1`. -/
theorem shellOf7_cogito_value (rs : ShellThresholds) (a : ℝ)
    (ha : shellOf7 rs ShellIndex7.cogito a) :
    a = 1 :=
  ha

/-- Outer-shell scalar members are exactly in the low-correlation interval
    `[0, r_5)`. -/
theorem shellOf7_outer_bound (rs : ShellThresholds) (a : ℝ)
    (ha : shellOf7 rs ShellIndex7.outer a) :
    0 ≤ a ∧ a < rs.r 5 :=
  ha

/-- **Same-shell bound** (the tractable load-bearing case of Proposition 5.3.1).

    If two profile values `a, b` both lie in the half-open interval
    `[r_(i+1), r_i)` for the same shell index, then their distance is
    strictly bounded by the shell's gap. -/
theorem sameShellBound (rs : ShellThresholds) (a b : ℝ)
    (i : Fin 5)
    (ha_lower : rs.r ⟨i.val + 1, by omega⟩ ≤ a)
    (ha_upper : a < rs.r ⟨i.val, by omega⟩)
    (hb_lower : rs.r ⟨i.val + 1, by omega⟩ ≤ b)
    (hb_upper : b < rs.r ⟨i.val, by omega⟩) :
    |a - b| < rs.r ⟨i.val, by omega⟩ - rs.r ⟨i.val + 1, by omega⟩ := by
  rcases le_or_lt a b with hab | hab
  · rw [abs_of_nonpos (by linarith)]
    linarith
  · rw [abs_of_pos (by linarith)]
    linarith

/-- Same-shell bound stated through the `shellOf` predicate. -/
theorem sameShellBound_of_shellOf (rs : ShellThresholds) (a b : ℝ)
    (i : Fin 5) (ha : shellOf rs i a) (hb : shellOf rs i b) :
    |a - b| < rs.r ⟨i.val, by omega⟩ - rs.r ⟨i.val + 1, by omega⟩ :=
  sameShellBound rs a b i ha.1 ha.2 hb.1 hb.2

/-- Interior-shell naming bridge for the same-shell distance bound. -/
theorem sameInteriorShell_distance_bound
    (rs : ShellThresholds) (a b : ℝ) (i : Fin 5)
    (ha : shellOf rs i a) (hb : shellOf rs i b) :
    |a - b| < rs.r ⟨i.val, by omega⟩ - rs.r ⟨i.val + 1, by omega⟩ :=
  sameShellBound_of_shellOf rs a b i ha hb

/-- Conservative cross-interior-shell bound.

    Under the current interior-only shell predicate, every shell member lies in
    `[0, 1]`, so any two interior-shell values have distance at most `1`.
    This is weaker than the full shell-stratified estimate but does not require
    additional boundary-shell conventions. -/
theorem interiorShell_pair_bound
    (rs : ShellThresholds) (a b : ℝ) (i j : Fin 5)
    (ha : shellOf rs i a) (hb : shellOf rs j b) :
    |a - b| ≤ 1 := by
  have ha0 : 0 ≤ a := shellOf_nonneg rs i a ha
  have ha1 : a ≤ 1 := shellOf_le_one rs i a ha
  have hb0 : 0 ≤ b := shellOf_nonneg rs j b hb
  have hb1 : b ≤ 1 := shellOf_le_one rs j b hb
  rw [abs_sub_le_iff]
  constructor <;> linarith

/-- Same-shell bound for the cogito singleton shell. -/
theorem sameCogitoShell_bound (rs : ShellThresholds) (a b : ℝ)
    (ha : shellOf7 rs ShellIndex7.cogito a)
    (hb : shellOf7 rs ShellIndex7.cogito b) :
    |a - b| = 0 := by
  rw [shellOf7_cogito_value rs a ha, shellOf7_cogito_value rs b hb, sub_self, abs_zero]

/-- Same-shell bound for the outer low-correlation shell. -/
theorem sameOuterShell_bound (rs : ShellThresholds) (a b : ℝ)
    (ha : shellOf7 rs ShellIndex7.outer a)
    (hb : shellOf7 rs ShellIndex7.outer b) :
    |a - b| < rs.r 5 := by
  rcases le_or_lt a b with hab | hab
  · rw [abs_of_nonpos (by linarith)]
    linarith [ha.1, hb.2]
  · rw [abs_of_pos (by linarith)]
    linarith [ha.2, hb.1]

/-- Endpoint form for distances between two interval-bounded scalar values. -/
theorem abs_sub_le_max_endpoint_abs
    {l₁ u₁ l₂ u₂ a b : ℝ}
    (ha_lower : l₁ ≤ a) (ha_upper : a ≤ u₁)
    (hb_lower : l₂ ≤ b) (hb_upper : b ≤ u₂) :
    |a - b| ≤ max |u₁ - l₂| |l₁ - u₂| := by
  rw [abs_sub_le_iff]
  constructor
  · exact le_trans (by linarith)
      (le_trans (le_abs_self _) (le_max_left _ _))
  · have h_abs : u₂ - l₁ ≤ |l₁ - u₂| := by
      have := neg_le_abs (l₁ - u₂)
      linarith
    exact le_trans (by linarith)
      (le_trans h_abs (le_max_right _ _))

/-- Full boundary-aware scalar shell-stratified bound.

    This is the pointwise content of Proposition 5.3.1 under the explicit
    seven-shell convention: shell 0 is the cogito singleton, shells 1-5 are
    the half-open threshold intervals, and shell 6 is `[0, r_5)`. -/
theorem fullShellStratifiedBound
    (rs : ShellThresholds) (a b : ℝ) (i j : ShellIndex7)
    (ha : shellOf7 rs i a) (hb : shellOf7 rs j b) :
    |a - b| ≤
      max |shellUpperEndpoint rs i - shellLowerEndpoint rs j|
        |shellLowerEndpoint rs i - shellUpperEndpoint rs j| :=
  abs_sub_le_max_endpoint_abs
    (shellOf7_lower_le rs i a ha) (shellOf7_le_upper rs i a ha)
    (shellOf7_lower_le rs j b hb) (shellOf7_le_upper rs j b hb)

/-- Endpoint-bound naming bridge for the full boundary-aware scalar theorem. -/
theorem fullShellStratifiedBound_endpointBound
    (rs : ShellThresholds) (a b : ℝ) (i j : ShellIndex7)
    (ha : shellOf7 rs i a) (hb : shellOf7 rs j b) :
    |a - b| ≤ shellEndpointBound rs i j := by
  simpa [shellEndpointBound] using fullShellStratifiedBound rs a b i j ha hb

/-- The endpoint shell bound is nonnegative. -/
theorem shellEndpointBound_nonneg
    (rs : ShellThresholds) (i j : ShellIndex7) :
    0 ≤ shellEndpointBound rs i j := by
  unfold shellEndpointBound
  exact le_trans (abs_nonneg _) (le_max_left _ _)

/-- The cogito/cogito endpoint bound is zero. -/
theorem shellEndpointBound_self_cogito
    (rs : ShellThresholds) :
    shellEndpointBound rs ShellIndex7.cogito ShellIndex7.cogito = 0 := by
  norm_num [shellEndpointBound, shellLowerEndpoint, shellUpperEndpoint]

/-- The endpoint shell bound is symmetric in its shell indices. -/
theorem shellEndpointBound_symm
    (rs : ShellThresholds) (i j : ShellIndex7) :
    shellEndpointBound rs i j = shellEndpointBound rs j i := by
  unfold shellEndpointBound
  rw [abs_sub_comm (shellUpperEndpoint rs j) (shellLowerEndpoint rs i),
    abs_sub_comm (shellLowerEndpoint rs j) (shellUpperEndpoint rs i)]
  exact max_comm _ _

/-- Legacy marker for Proposition 5.3.1, retained only for compatibility with
    older Rosetta inventories.

    The boundary-aware pointwise scalar theorem is now
    `fullShellStratifiedBound`; shared-domain profile corollaries are exported
    through endpoint-bound theorems below. Union-domain shell bounds are
    encoded by `dInfUnion_le_of_pointwise`, `dInfUnion_le_of_pointwise_union`,
    `dInfUnion_le_shellEndpointBound_zeroExtend`,
    `dInfUnion_le_threeWayMax_shellEndpointBound`, and
    `dInfUnion_le_of_pointwise_shellEndpointBound`. The `outer` shell absorbs
    `0` on each profile-only portion of the union; see the three-way-max
    corollary for the natural source-paper hypothesis shape. -/
def shellStratifiedBound_deferred : Prop := True

/-- Profile-level shared-distance bound from an explicit pointwise bound.

    This theorem isolates the supremum step used by shell-stability corollaries:
    when all shared-domain pointwise zero-extension distances are bounded by a
    nonnegative real `B`, the shared `L∞` distance is bounded by `ofReal B`. -/
theorem shellStableDistanceBound_of_pointwise
    (f g : ScalarProfile α)
    (h_nonempty : (f.domain ∩ g.domain).Nonempty)
    (B : ℝ)
    (h_pointwise :
      ∀ x ∈ f.domain ∩ g.domain,
        |f.zeroExtend x - g.zeroExtend x| ≤ B) :
    dInfShared f g ≤ ENNReal.ofReal B := by
  unfold dInfShared
  rw [if_pos h_nonempty]
  apply iSup_le
  intro x
  apply iSup_le
  intro hx
  exact ENNReal.ofReal_le_ofReal (h_pointwise x hx)

/-- Shared-domain shell bound stated directly over zero-extended values.

    If every shared-domain zero-extended value of `f` lies in shell `i` and
    every shared-domain zero-extended value of `g` lies in shell `j`, then the
    shared `L∞` distance is bounded by the seven-shell endpoint bound. -/
theorem dInfShared_le_shellEndpointBound_zeroExtend
    (rs : ShellThresholds)
    (f g : ScalarProfile α)
    (i j : ShellIndex7)
    (h_nonempty : (f.domain ∩ g.domain).Nonempty)
    (hf_shell :
      ∀ x ∈ f.domain ∩ g.domain,
        shellOf7 rs i (f.zeroExtend x))
    (hg_shell :
      ∀ x ∈ f.domain ∩ g.domain,
        shellOf7 rs j (g.zeroExtend x)) :
    dInfShared f g ≤ ENNReal.ofReal (shellEndpointBound rs i j) := by
  apply shellStableDistanceBound_of_pointwise f g h_nonempty
  intro x hx
  exact fullShellStratifiedBound_endpointBound rs
    (f.zeroExtend x) (g.zeroExtend x) i j (hf_shell x hx) (hg_shell x hx)

/-- Shared-domain shell bound with shell hypotheses over profile-domain
    subtype values. -/
theorem dInfShared_le_shellEndpointBound
    (rs : ShellThresholds)
    (f g : ScalarProfile α)
    (i j : ShellIndex7)
    (h_nonempty : (f.domain ∩ g.domain).Nonempty)
    (hf_shell :
      ∀ x ∈ f.domain ∩ g.domain,
        ∀ hfx : x ∈ f.domain,
          shellOf7 rs i (f.toFun ⟨x, hfx⟩))
    (hg_shell :
      ∀ x ∈ f.domain ∩ g.domain,
        ∀ hgx : x ∈ g.domain,
          shellOf7 rs j (g.toFun ⟨x, hgx⟩)) :
    dInfShared f g ≤ ENNReal.ofReal (shellEndpointBound rs i j) := by
  apply dInfShared_le_shellEndpointBound_zeroExtend rs f g i j h_nonempty
  · intro x hx
    rw [f.zeroExtend_of_mem x hx.1]
    exact hf_shell x hx hx.1
  · intro x hx
    rw [g.zeroExtend_of_mem x hx.2]
    exact hg_shell x hx hx.2

/-- Shared-domain shell bound with pointwise shell indices allowed to vary,
    provided each pointwise endpoint bound is uniformly bounded by `B`. -/
theorem dInfShared_le_of_pointwise_shellEndpointBound
    (rs : ShellThresholds)
    (f g : ScalarProfile α)
    (B : ℝ)
    (h_nonempty : (f.domain ∩ g.domain).Nonempty)
    (h_point :
      ∀ x ∈ f.domain ∩ g.domain,
        ∃ i j,
          shellOf7 rs i (f.zeroExtend x) ∧
          shellOf7 rs j (g.zeroExtend x) ∧
          shellEndpointBound rs i j ≤ B) :
    dInfShared f g ≤ ENNReal.ofReal B := by
  apply shellStableDistanceBound_of_pointwise f g h_nonempty
  intro x hx
  rcases h_point x hx with ⟨i, j, hf_shell, hg_shell, hB⟩
  exact le_trans
    (fullShellStratifiedBound_endpointBound rs
      (f.zeroExtend x) (g.zeroExtend x) i j hf_shell hg_shell)
    hB

/-- Same-interior-shell shared-profile bound as an endpoint-bound corollary. -/
theorem dInfShared_le_sameInteriorShellEndpointBound
    (rs : ShellThresholds)
    (f g : ScalarProfile α)
    (i : Fin 5)
    (h_nonempty : (f.domain ∩ g.domain).Nonempty)
    (hf_shell :
      ∀ x ∈ f.domain ∩ g.domain,
        ∀ hfx : x ∈ f.domain,
          shellOf rs i (f.toFun ⟨x, hfx⟩))
    (hg_shell :
      ∀ x ∈ f.domain ∩ g.domain,
        ∀ hgx : x ∈ g.domain,
          shellOf rs i (g.toFun ⟨x, hgx⟩)) :
    dInfShared f g ≤
      ENNReal.ofReal
        (shellEndpointBound rs (ShellIndex7.interior i) (ShellIndex7.interior i)) := by
  exact dInfShared_le_shellEndpointBound rs f g
    (ShellIndex7.interior i) (ShellIndex7.interior i) h_nonempty
    hf_shell hg_shell

/-- **Corollary 5.3.2 simplified** (shell-stable distance vanishing).

    If two profiles `f` and `g` have all shared-subdomain values in a
    single shell `i`, then `dInfShared f g` is bounded above by the
    shell's gap. -/
theorem shellStableDistanceVanishing_simple
    (rs : ShellThresholds) (f g : ScalarProfile α) (i : Fin 5)
    (h_nonempty : (f.domain ∩ g.domain).Nonempty)
    (h_f_in_shell : ∀ x ∈ f.domain ∩ g.domain,
      ∀ h : x ∈ f.domain,
        shellOf rs i (f.toFun ⟨x, h⟩))
    (h_g_in_shell : ∀ x ∈ f.domain ∩ g.domain,
      ∀ h : x ∈ g.domain,
        shellOf rs i (g.toFun ⟨x, h⟩)) :
    dInfShared f g ≤
      ENNReal.ofReal (rs.r ⟨i.val, by omega⟩ - rs.r ⟨i.val + 1, by omega⟩) := by
  unfold dInfShared
  rw [if_pos h_nonempty]
  apply iSup_le
  intro x
  apply iSup_le
  intro hx
  by_cases hfx : x ∈ f.domain
  · by_cases hgx : x ∈ g.domain
    · have hf_shell := h_f_in_shell x hx hfx
      have hg_shell := h_g_in_shell x hx hgx
      rw [f.zeroExtend_of_mem x hfx, g.zeroExtend_of_mem x hgx]
      have h_bound : |f.toFun ⟨x, hfx⟩ - g.toFun ⟨x, hgx⟩| <
                     rs.r ⟨i.val, by omega⟩ - rs.r ⟨i.val + 1, by omega⟩ :=
        sameShellBound_of_shellOf rs _ _ i hf_shell hg_shell
      apply ENNReal.ofReal_le_ofReal
      linarith
    · exact absurd hx.2 hgx
  · exact absurd hx.1 hfx

/-! ## Union-form shell-bound corollaries

The lemmas below are the union-domain analogues of the `dInfShared_le_*`
family. They build on `dInfUnion`, which (per `Pointwise.lean`) is the
supremum `⨆ x : α, ENNReal.ofReal |f.zeroExtend x - g.zeroExtend x|` over
the universal content-type — outside `f.domain ∪ g.domain` both
zero-extensions are `0`, so the contribution vanishes.

Reference: profile_comparison_v0_2.md §5.3 (union-form shell-stability
bounds via zero-extension and outer-shell absorption). -/

/-- Profile-level union-distance bound from an explicit pointwise bound.

    Parallel to `shellStableDistanceBound_of_pointwise` but for `dInfUnion`.
    No non-emptiness hypothesis is needed because `dInfUnion`'s supremum
    indexes over the universal `α`, with absent values contributing `0`. -/
theorem dInfUnion_le_of_pointwise
    (f g : ScalarProfile α) (B : ℝ)
    (h_pointwise : ∀ x : α, |f.zeroExtend x - g.zeroExtend x| ≤ B) :
    dInfUnion f g ≤ ENNReal.ofReal B := by
  unfold dInfUnion
  apply iSup_le
  intro x
  exact ENNReal.ofReal_le_ofReal (h_pointwise x)

/-- Variant of `dInfUnion_le_of_pointwise` whose hypothesis is restricted
    to `f.domain ∪ g.domain`.

    Outside the union both zero-extensions are `0`, so the pointwise
    difference is `0` and is bounded by any nonnegative `B`. -/
theorem dInfUnion_le_of_pointwise_union
    (f g : ScalarProfile α) (B : ℝ) (hB : 0 ≤ B)
    (h_pointwise :
      ∀ x, x ∈ f.domain ∪ g.domain →
        |f.zeroExtend x - g.zeroExtend x| ≤ B) :
    dInfUnion f g ≤ ENNReal.ofReal B := by
  apply dInfUnion_le_of_pointwise f g B
  intro x
  by_cases hx : x ∈ f.domain ∪ g.domain
  · exact h_pointwise x hx
  · have hfx : x ∉ f.domain := fun h => hx (Or.inl h)
    have hgx : x ∉ g.domain := fun h => hx (Or.inr h)
    rw [f.zeroExtend_of_not_mem x hfx, g.zeroExtend_of_not_mem x hgx]
    simpa using hB

/-- Union-domain shell bound stated directly over zero-extended values.

    If every zero-extended value of `f` lies in shell `i` and every
    zero-extended value of `g` lies in shell `j` (under thresholds `rs`),
    then the union `L∞` distance is bounded by the seven-shell endpoint
    bound.

    The hypotheses range over all of `α`. For `x ∉ f.domain` the
    zero-extended value is `0`, so the typical caller takes `i` or `j`
    equal to `ShellIndex7.outer` on the corresponding complement.
    Use `dInfUnion_le_threeWayMax_shellEndpointBound` for the natural
    source-paper hypothesis shape. -/
theorem dInfUnion_le_shellEndpointBound_zeroExtend
    (rs : ShellThresholds) (f g : ScalarProfile α) (i j : ShellIndex7)
    (hf_shell : ∀ x : α, shellOf7 rs i (f.zeroExtend x))
    (hg_shell : ∀ x : α, shellOf7 rs j (g.zeroExtend x)) :
    dInfUnion f g ≤ ENNReal.ofReal (shellEndpointBound rs i j) := by
  apply dInfUnion_le_of_pointwise f g (shellEndpointBound rs i j)
  intro x
  exact fullShellStratifiedBound_endpointBound rs
    (f.zeroExtend x) (g.zeroExtend x) i j (hf_shell x) (hg_shell x)

/-- Union-domain shell bound with shell hypotheses stated separately on
    each profile's own domain subtype, paying for the asymmetry with a
    three-way max of endpoint bounds.

    On `f.domain ∩ g.domain` the relevant bound is `shellEndpointBound rs i j`;
    on `f.domain \ g.domain` the absent profile contributes `0` (in shell
    `outer`), giving bound `shellEndpointBound rs i outer`; symmetrically
    for `g.domain \ f.domain`. The overall bound is the max of these
    three. -/
theorem dInfUnion_le_threeWayMax_shellEndpointBound
    (rs : ShellThresholds) (f g : ScalarProfile α) (i j : ShellIndex7)
    (hf_shell :
      ∀ x, ∀ hfx : x ∈ f.domain,
        shellOf7 rs i (f.toFun ⟨x, hfx⟩))
    (hg_shell :
      ∀ x, ∀ hgx : x ∈ g.domain,
        shellOf7 rs j (g.toFun ⟨x, hgx⟩)) :
    dInfUnion f g ≤
      ENNReal.ofReal
        (max (shellEndpointBound rs i j)
          (max (shellEndpointBound rs i ShellIndex7.outer)
            (shellEndpointBound rs ShellIndex7.outer j))) := by
  set B :=
    max (shellEndpointBound rs i j)
      (max (shellEndpointBound rs i ShellIndex7.outer)
        (shellEndpointBound rs ShellIndex7.outer j))
  have hB : 0 ≤ B :=
    le_trans (shellEndpointBound_nonneg rs i j) (le_max_left _ _)
  have h_zero_outer : shellOf7 rs ShellIndex7.outer (0 : ℝ) := by
    refine ⟨le_refl 0, rs.r_five_pos⟩
  apply dInfUnion_le_of_pointwise f g B
  intro x
  by_cases hfx : x ∈ f.domain
  · by_cases hgx : x ∈ g.domain
    · -- both domains
      have hf := hf_shell x hfx
      have hg := hg_shell x hgx
      rw [f.zeroExtend_of_mem x hfx, g.zeroExtend_of_mem x hgx]
      exact le_trans
        (fullShellStratifiedBound_endpointBound rs _ _ i j hf hg)
        (le_max_left _ _)
    · -- f only; g.zeroExtend x = 0 ∈ outer
      have hf := hf_shell x hfx
      rw [f.zeroExtend_of_mem x hfx, g.zeroExtend_of_not_mem x hgx]
      exact le_trans
        (fullShellStratifiedBound_endpointBound rs _ _ i ShellIndex7.outer
          hf h_zero_outer)
        (le_trans (le_max_left _ _) (le_max_right _ _))
  · by_cases hgx : x ∈ g.domain
    · -- g only; f.zeroExtend x = 0 ∈ outer
      have hg := hg_shell x hgx
      rw [f.zeroExtend_of_not_mem x hfx, g.zeroExtend_of_mem x hgx]
      exact le_trans
        (fullShellStratifiedBound_endpointBound rs _ _ ShellIndex7.outer j
          h_zero_outer hg)
        (le_trans (le_max_right _ _) (le_max_right _ _))
    · -- neither; both extensions are 0
      rw [f.zeroExtend_of_not_mem x hfx, g.zeroExtend_of_not_mem x hgx]
      simpa using hB

/-- Union-domain shell bound with pointwise shell indices allowed to vary,
    provided each pointwise endpoint bound is bounded by `B`.

    Parallel to `dInfShared_le_of_pointwise_shellEndpointBound`. -/
theorem dInfUnion_le_of_pointwise_shellEndpointBound
    (rs : ShellThresholds) (f g : ScalarProfile α) (B : ℝ)
    (h_point :
      ∀ x : α,
        ∃ i j,
          shellOf7 rs i (f.zeroExtend x) ∧
          shellOf7 rs j (g.zeroExtend x) ∧
          shellEndpointBound rs i j ≤ B) :
    dInfUnion f g ≤ ENNReal.ofReal B := by
  apply dInfUnion_le_of_pointwise f g B
  intro x
  rcases h_point x with ⟨i, j, hf, hg, hle⟩
  exact le_trans
    (fullShellStratifiedBound_endpointBound rs _ _ i j hf hg) hle

end TLICA.ProfileComparison.ShellRefinement
