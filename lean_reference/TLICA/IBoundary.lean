/-
TLICA.IBoundary — The I/not-I boundary as a derived structure.

Encodes §9 of the orphan_cluster_v0_1.md working paper: the I/not-I boundary
as a derived sub-region of the asymptotic content domain. The boundary
emerges from Mode A / Mode C operation (PtCns-driven) and is the structural
region of contestable PtCns assignment.

Reference:
  - 2_access_and_development.md §4.5 (theoretical statement).
  - orphan_cluster_v0_1.md §9 (foundation-ready definition and axioms).
-/

import TLICA.PtCns

namespace TLICA.IBoundary

open TLICA.Profile TLICA.MSI TLICA.PtCns
open Classical

variable {α : Type*}

/-- The I/not-I boundary at modeling I `m` and time `t`, encoded as the
    sub-region of the profile's domain where Mode A and Mode C both
    operate as candidates with active selection.

    Reference: orphan_cluster_v0_1.md Candidate 9.2.3. -/
def boundary (msi : MSI α) (p : PtCns msi) : Set ↥msi.profile.domain :=
  p.positiveContents ∪ p.negativeContents

/-- The boundary excludes PtCns-neutral content. -/
theorem boundary_excludes_neutral (msi : MSI α) (p : PtCns msi) :
    boundary msi p ∩ p.neutralContents = ∅ := by
  unfold boundary
  ext x
  simp [Set.mem_inter_iff, Set.mem_union, Set.mem_empty_iff_false,
        PtCns.positiveContents, PtCns.negativeContents, PtCns.neutralContents,
        Set.mem_setOf_eq]
  intro h1 h2
  rcases h1 with h | h
  all_goals { rw [h] at h2; cases h2 }

/-- **Axiom 9.3.2**: the cogito is in the boundary's PtCns-positive part,
    hence not at the boundary's *edge* — but it is in `boundary`. The
    architecture's "cogito interiority" is captured by the cogito being
    in PtCns-positive (Mode C), not in the contestable region.

    A more refined boundary that excludes interior positive contents would
    require additional structure. -/
theorem cogito_in_boundary (msi : MSI α) (p : PtCns msi) :
    msi.cogito ∈ boundary msi p := by
  unfold boundary
  left
  exact p.cogito_in_positive

/-- Membership in the foundation boundary is exactly PtCns-positive or
    PtCns-negative evaluation. -/
theorem mem_boundary_iff (msi : MSI α) (p : PtCns msi)
    (x : ↥msi.profile.domain) :
    x ∈ boundary msi p ↔
      p.eval x = ConsistencyEval.preserve ∨ p.eval x = ConsistencyEval.damage := by
  unfold boundary PtCns.positiveContents PtCns.negativeContents
  simp [Set.mem_union]

/-- Boundary contents are not PtCns-neutral. -/
theorem boundary_not_neutral (msi : MSI α) (p : PtCns msi)
    (x : ↥msi.profile.domain) (h : x ∈ boundary msi p) :
    p.eval x ≠ ConsistencyEval.neutral := by
  rw [mem_boundary_iff] at h
  intro h_neutral
  rcases h with h_preserve | h_damage
  · rw [h_preserve] at h_neutral
    cases h_neutral
  · rw [h_damage] at h_neutral
    cases h_neutral

/-- An alternative refined boundary: the region of *contestable* PtCns
    assignment, excluding interior positive and interior negative contents.

    This is a more nuanced characterization corresponding to
    `Candidate 9.2.3` strictly. Foundation may use either depending on
    application. -/
def contestableBoundary (msi : MSI α) (p : PtCns msi) : Set ↥msi.profile.domain :=
  -- Stub for the more nuanced definition; the foundation default uses
  -- `boundary` above.
  boundary msi p

end TLICA.IBoundary
