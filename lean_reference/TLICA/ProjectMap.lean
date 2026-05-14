/-
TLICA.ProjectMap — The future-state projection map (deterministic variant).

Encodes §5 of the orphan_cluster_v0_1.md working paper. The foundation
default per §5.4.1 is the deterministic Project map; the stochastic
variant (with ProbabilityMeasure codomain) is deferred to a future round.

Reference:
  - 4_derived_concepts_and_predictions.md §10.7 (theoretical statement).
  - orphan_cluster_v0_1.md §5 (foundation-ready definitions and axioms).
-/

import TLICA.Profile

namespace TLICA.ProjectMap

open TLICA.Profile

variable {α Act : Type*}

/-- Degenerate/default foundation action type. The v0.4 projection structure is
    parameterized by an arbitrary action type; this singleton-like wrapper
    preserves the old foundation default case. -/
structure Action (α : Type*) where
  /-- The old default action carried only unit data. -/
  data : Unit

/-- Unit-valued default action type for the degenerate foundation case. -/
abbrev DefaultAction (_α : Type*) := Unit

/-- The "no action" / null action. -/
def Action.noAction : Action α := ⟨()⟩

/-- The deterministic future-state projection map.

    Given a current profile and a candidate action, produces the projected
    profile at some forward horizon. Stochasticity (where applications need
    it) is captured by parameterizing the action space.

    Reference: orphan_cluster_v0_1.md Definition 5.2.1 (deterministic variant). -/
structure ProjectMap (α Act : Type*) where
  /-- The no-action / null action for this action space. -/
  noAction : Act
  /-- The projection function. -/
  project : Act → ScalarProfile α → ScalarProfile α
  /-- **Axiom 5.3.1**: the no-action projection equals the natural-dynamics
      evolution of the current profile.
      We state it abstractly: there is *some* natural-dynamics function and
      `project noAction` equals it. -/
  identity_action_natural :
    ∃ (naturalDynamics : ScalarProfile α → ScalarProfile α),
      ∀ P, project noAction P = naturalDynamics P

/-- Compatibility abbreviation for the old singleton-action foundation
    projection map. New code should prefer `ProjectMap α Act`. -/
abbrev DefaultProjectMap (α : Type*) := ProjectMap α (Action α)

/-- Compatibility abbreviation for the simplest unit-carrier default projection
    map. This avoids the old wrapper when no wrapper compatibility is needed. -/
abbrev UnitDefaultProjectMap (α : Type*) := ProjectMap α (DefaultAction α)

namespace ProjectMap

variable {α Act : Type*}

/-- The no-action projection is well-defined (existence is automatic since
    `project` is total). -/
theorem noAction_projects (proj : ProjectMap α Act) (P : ScalarProfile α) :
    ∃ P', proj.project proj.noAction P = P' :=
  ⟨proj.project proj.noAction P, rfl⟩

end ProjectMap

end TLICA.ProjectMap
