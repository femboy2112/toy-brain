/-
TLICA.Modes — The three modes of I-development as evolutionary operators.

Encodes §8 of the orphan_cluster_v0_1.md working paper: Modes A
(differentiation), B (self-modeling / reflective), and C (integration) as
typed operators on the apparatus state, with PtCns-triggered selection.

Reference:
  - 2_access_and_development.md §4 (theoretical statement).
  - orphan_cluster_v0_1.md §8 (foundation-ready definitions and axioms).
-/

import TLICA.PtCns

namespace TLICA.Modes

open TLICA.Profile TLICA.MSI TLICA.PtCns

/-- The four possible apparatus operations triggered by PtCns evaluation.

    * `modeA`: differentiation (triggered by `ConsistencyEval.damage`).
    * `modeC`: integration (triggered by `ConsistencyEval.preserve`).
    * `neutral`: identity-neutral encapsulation (triggered by `ConsistencyEval.neutral`).
    * `modeB`: self-modeling / reflective access (parallel to A/C, not triggered
      by PtCns but by Mode B reflective capacity).

    Reference: orphan_cluster_v0_1.md §8.2. -/
inductive ModeOp where
  | modeA
  | modeB
  | modeC
  | neutral
  deriving DecidableEq, Repr

namespace ModeOp

/-- The mode operation triggered by a given PtCns evaluation. -/
def fromEval : ConsistencyEval → ModeOp
  | ConsistencyEval.damage => modeA
  | ConsistencyEval.neutral => neutral
  | ConsistencyEval.preserve => modeC

@[simp] theorem fromEval_damage : fromEval ConsistencyEval.damage = modeA := rfl
@[simp] theorem fromEval_neutral : fromEval ConsistencyEval.neutral = neutral := rfl
@[simp] theorem fromEval_preserve : fromEval ConsistencyEval.preserve = modeC := rfl

/-- The cogito always triggers Mode C (integration), since the cogito is
    always PtCns-preserving (Axiom 7.3.1). -/
theorem cogito_triggers_modeC {α : Type*} (msi : MSI α) (p : PtCns msi) :
    fromEval (p.eval msi.cogito) = modeC := by
  rw [p.cogito_invariance]
  rfl

end ModeOp

end TLICA.Modes
