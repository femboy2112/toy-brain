# PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_ROADMAP.md

## Purpose

This roadmap combines three post-Phase-3.9 follow-ups into one review-gated campaign:

```text
A. Operational Hardening
B. Persistence Observability
C. Autosave Policy
```

The repo already has explicit SQLite persistence from Phase 3.9. The next goal is to make persistence practically safe to operate: visible, verifiable, recoverable, and eventually autosavable without turning autosave into a hidden mutation path.

---

## Baseline

```text
Catalog: v0.17
Counts: 187 REQUIRED / 69 STRUCTURAL / 10 NOT-EXERCISED / 12 DEFERRED / 13 OBSERVED
Latest complete campaign: Phase 3.9 Persistent Session Store
```

Phase 3.9 gave:

```text
--session-db
--load-session
--no-load-session
/save-session
/load-session
brain/ui/persistence.py
exact Fraction round-trip
builder-routed load
COGITO_ID protection
transactional save
read-only load
no sqlite3.Connection on OperatorSession
no autosave
```

---

## Phase 3.10a — Operational Hardening

Target:

```text
/session-status
/db-status
/db-verify
/db-backup
```

These commands help the operator understand and protect the persistence store before trusting it.

Rules:

```text
status commands are read-only
verify commands do not activate saved state
backup is explicit only
failure is bounded local UI status/error
no tick call
```

---

## Phase 3.10b — Persistence Observability

Target:

```text
/db-summary
/profile-summary
/stream-db-summary
/db-diff
```

These commands expose the saved DB state without loading it into the live session.

Rules:

```text
read-only sqlite access
no live BrainState mutation
no session replacement
exact Fraction display as strings
bounded display rows
```

---

## Phase 3.10c — Autosave Policy

Target:

```text
/autosave-status
/autosave-enable
/autosave-disable
--autosave-mode off|after-successful-mutation
```

Autosave is useful only after operational hardening and observability exist. The campaign therefore keeps autosave behind a second review gate.

Rules:

```text
default off
explicit opt-in only
requires configured session DB
finite trigger set
no background hooks
no autosave during tick()
no autosave after failed commands
no autosave after read-only commands
autosave failure preserves live state
```

---

## Recommended sequence

```text
1. Sync mission/campaign files
2. Plan combined Phase 3.10
3. Catalog and implement operational hardening + observability
4. Audit operational hardening + observability
5. Plan autosave separately
6. Catalog and implement opt-in autosave
7. Audit autosave
8. Integrated Phase 3.10 audit
9. Final PR
```

---

## Completion condition

The campaign is complete when:

```text
full gate is green
status / verify / summary / diff / backup work as finite typed commands
autosave is off by default
autosave can be explicitly enabled/disabled if the autosave phase is accepted
autosave failure is local and bounded
no hidden persistence path exists
PR is opened and not merged without approval
```
