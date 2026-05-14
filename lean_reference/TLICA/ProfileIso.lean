/-
TLICA.ProfileIso — Optional profile-isomorphism coherence.

This module records a lightweight extensional coherence relation between
profiles without changing `ScalarProfile`. It is stronger than mere domain
equality: domains agree extensionally, and profile values agree on any shared
membership proofs.
-/

import TLICA.Profile

namespace TLICA.ProfileIso

open TLICA.Profile

variable {α : Type*}

/-- Extensional isomorphism/coherence between scalar profiles. -/
structure ProfileIso (P Q : ScalarProfile α) where
  /-- The profile domains agree extensionally. -/
  dom_iff : ∀ x, x ∈ P.domain ↔ x ∈ Q.domain
  /-- Profile values agree for any membership proofs in the matching domains. -/
  val_eq :
    ∀ x (hP : x ∈ P.domain) (hQ : x ∈ Q.domain),
      P.toFun ⟨x, hP⟩ = Q.toFun ⟨x, hQ⟩

namespace ProfileIso

/-- Domain membership can be transported across a profile isomorphism. -/
theorem dom_mem_iff {P Q : ScalarProfile α} (h : ProfileIso P Q) (x : α) :
    x ∈ P.domain ↔ x ∈ Q.domain :=
  h.dom_iff x

/-- Profile values agree after transporting a left-domain membership proof. -/
theorem val_eq_left {P Q : ScalarProfile α} (h : ProfileIso P Q)
    {x : α} (hP : x ∈ P.domain) :
    P.toFun ⟨x, hP⟩ = Q.toFun ⟨x, (h.dom_iff x).1 hP⟩ :=
  h.val_eq x hP ((h.dom_iff x).1 hP)

/-- Profile values agree after transporting a right-domain membership proof. -/
theorem val_eq_right {P Q : ScalarProfile α} (h : ProfileIso P Q)
    {x : α} (hQ : x ∈ Q.domain) :
    P.toFun ⟨x, (h.dom_iff x).2 hQ⟩ = Q.toFun ⟨x, hQ⟩ :=
  h.val_eq x ((h.dom_iff x).2 hQ) hQ

/-- Profile isomorphism is reflexive. -/
def refl (P : ScalarProfile α) : ProfileIso P P where
  dom_iff := by
    intro x
    exact Iff.rfl
  val_eq := by
    intro x hP _hQ
    rfl

/-- Profile isomorphism is symmetric. -/
def symm {P Q : ScalarProfile α} (h : ProfileIso P Q) : ProfileIso Q P where
  dom_iff := by
    intro x
    exact (h.dom_iff x).symm
  val_eq := by
    intro x hQ hP
    exact (h.val_eq x hP hQ).symm

/-- Profile isomorphism is transitive. -/
def trans {P Q R : ScalarProfile α}
    (hPQ : ProfileIso P Q) (hQR : ProfileIso Q R) : ProfileIso P R where
  dom_iff := by
    intro x
    exact Iff.trans (hPQ.dom_iff x) (hQR.dom_iff x)
  val_eq := by
    intro x hP hR
    have hQ : x ∈ Q.domain := (hPQ.dom_iff x).1 hP
    exact Eq.trans (hPQ.val_eq x hP hQ) (hQR.val_eq x hQ hR)

end ProfileIso

end TLICA.ProfileIso
