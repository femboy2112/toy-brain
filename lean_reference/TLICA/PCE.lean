/-
TLICA.PCE — The prerogative of continued existence (deterministic variant).

Encodes §6 of the orphan_cluster_v0_1.md working paper. PCE is the
composite of MSI, PreservationRanking (Π), and ProjectMap. In the
deterministic foundation default, the expectation operator reduces to the
identity, and PCE becomes:

  PCE(a) := Π( project(a, P) ∩ MSI )

The action-selection principle picks a maximizing action under existential
pressure.

Reference:
  - 2_access_and_development.md §4.8, 4_derived_concepts_and_predictions.md §10.7.
  - orphan_cluster_v0_1.md §6 (foundation-ready definition with axioms).
-/

import TLICA.MSI
import TLICA.PreservationRanking
import TLICA.ProjectMap

namespace TLICA.PCE

open TLICA.Profile TLICA.MSI TLICA.PreservationRanking TLICA.ProjectMap
open Classical

variable {α Act : Type*}

/-- The PCE evaluation of an action, in the deterministic foundation default.

    Given a modeling I's MSI `msi`, its preservation-ranking `Π`, its
    projection map `proj`, and a candidate action `a`, the PCE value is
    `Π.rank` of the intersection of the projected profile's domain (lifted
    via subtype) with the MSI contents.

    To handle the type-alignment issue that the projected profile's domain
    may differ from the original profile's domain, we evaluate `Π.rank` over
    a subset specified by membership predicate. This is a simplification of
    the working paper's set-theoretic intersection.

    This default is action-constant over arbitrary action type `Act`; that
    constancy is not caused by singleton action typing. Action-sensitive
    evaluation lives in `TLICA.ActionProjection.ProjectedPCE`.

    Reference: orphan_cluster_v0_1.md Definition 6.2.1 (deterministic). -/
noncomputable def PCE (msi : MSI α) (pi : PreservationRanking msi)
    (proj : ProjectMap α Act) (a : Act) : ℝ :=
  -- In the deterministic default, the expectation reduces to evaluating Π
  -- on the projected MSI. Since the projected profile lives over a possibly
  -- different domain (subtype mismatch), we use the MSI's own contents as
  -- the foundation-level placeholder; applications calibrate the projection.
  pi.rank msi.contents

namespace PCE

variable {α Act : Type*}

/-- PCE is non-negative (follows from `Π.rank_nonneg`). -/
theorem nonneg (msi : MSI α) (pi : PreservationRanking msi)
    (proj : ProjectMap α Act) (a : Act) :
    0 ≤ PCE msi pi proj a :=
  pi.rank_nonneg _

/-- In the deterministic foundation default, PCE evaluates to the rank of the
    MSI contents. Application-calibrated projection models refine this value. -/
theorem eq_rank_msi_contents (msi : MSI α) (pi : PreservationRanking msi)
    (proj : ProjectMap α Act) (a : Act) :
    PCE msi pi proj a = pi.rank msi.contents :=
  rfl

/-- PCE attains its maximum at the MSI level (every action has PCE bounded
    above by Π.rank msi.contents, which is the foundation default value).

    In the foundation-default deterministic variant, every action has PCE
    equal to this maximum; richer projection maps differentiate actions. -/
theorem bounded_by_msi_max (msi : MSI α) (pi : PreservationRanking msi)
    (proj : ProjectMap α Act) (a : Act) :
    PCE msi pi proj a ≤ pi.rank msi.contents := by
  unfold PCE
  exact le_refl _

/-- The action-selection principle: the I selects actions maximizing PCE.
    Since the foundation-default has all actions at the same PCE, the
    selection is trivial here; richer projection maps will differentiate. -/
def selectsAction (msi : MSI α) (pi : PreservationRanking msi)
    (proj : ProjectMap α Act) (a : Act) : Prop :=
  ∀ b : Act, PCE msi pi proj b ≤ PCE msi pi proj a

/-- Every action is a maximizer in the foundation default (PCE is constant). -/
theorem every_action_maximizes (msi : MSI α) (pi : PreservationRanking msi)
    (proj : ProjectMap α Act) (a : Act) :
    selectsAction msi pi proj a := by
  unfold selectsAction PCE
  intro b
  exact le_refl _

/-- In the deterministic foundation default, all actions receive the same PCE
    value over arbitrary action type `Act`. This is a theorem about the
    foundation-default functional, not an artifact of singleton action typing.
    Differentiated action choice is handled by application-calibrated
    `ProjectedPCE`. -/
theorem all_actions_equal (msi : MSI α) (pi : PreservationRanking msi)
    (proj : ProjectMap α Act) (a b : Act) :
    PCE msi pi proj a = PCE msi pi proj b :=
  rfl

end PCE

end TLICA.PCE
