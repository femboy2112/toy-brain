"""Phase 3.10a Operational Hardening — placeholder.

This module is the Step 7 catalog-patch placeholder for Phase 3.10a
of the Operational Hardening + Persistence Observability + Autosave
campaign. It declares the hard boundaries the Step 8 implementation
must respect. No runtime is wired here yet; the operational-hardening
helpers (``session_status``, ``db_status``, ``db_verify``,
``db_backup``) and the typed report records (``SessionStatusReport``,
``DbStatusReport``, ``DbVerifyReport``, ``DbBackupReport``) land in
Step 8.

Hard boundaries pinned by
``PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_CORRIGENDA.md`` and
``PHASE3_10_OPS_OBSERVABILITY_CATALOG_PATCH_PLAN.md``:

* SQLite via the standard-library ``sqlite3`` module only — no
  ``pickle`` / ``shelve`` / ``marshal`` / ``dill`` / ``cloudpickle``
  / ``joblib`` / ``subprocess`` / ``socket`` / ``urllib`` / ``http``
  / ``requests`` / ``curses`` / ``brain.tick`` / ``brain.tlica``
  internals beyond what ``brain.ui.persistence`` re-exports /
  ``brain.llm``.
* ``/session-status`` reads in-memory ``OperatorSession`` fields
  only; no disk IO; no ``tick()``; no curses; no
  ``sqlite3.Connection``.
* ``/db-status`` opens the configured DB through
  ``sqlite3.connect("file:<path>?mode=ro", uri=True)`` inside a
  ``with conn:`` block, reads ``meta`` rows, closes; no
  ``tick()``; no swap; no builder call.
* ``/db-verify`` reuses ``load_session`` (the Phase 3.9 helper),
  immediately DROPS the returned candidate, and returns a typed
  ``DbVerifyReport``; the candidate is never assigned to the live
  ``OperatorSession``; the live session reference is unchanged by
  ``id()`` before and after the call.
* ``/db-backup`` uses ``sqlite3.Connection.backup()`` (page-faithful)
  from a ``mode=ro`` source connection to a write-mode destination
  connection inside ``with`` blocks; refuses to overwrite an
  existing destination unless ``force=True``; refuses URI-scheme
  destinations (``sqlite:``, ``file:``, ``http:``, ``https:``,
  ``ftp:``, ``ws:``, ``wss:``, ``data:``, ``gopher:``, ``ssh:``,
  ``git:``); refuses ``dest_path == source_path``; never modifies
  the source DB.
* New CLI short-circuit flags (``--db-status``, ``--db-verify``,
  ``--db-backup PATH``, ``--db-backup-force``) are mutually
  exclusive at argparse time and short-circuit after
  ``--check-terminal`` / ``--print-once`` but before
  ``parse_llm_runtime_args`` and curses initialization; exit
  code 0 on success and code 1 on failure.
* No ``sqlite3.Connection`` is stored on ``OperatorSession``; Phase
  3.10a adds NO new session field.
* No autosave entry point exists; no ``@atexit`` / signal /
  threading / asyncio autosave hook is registered; the Phase 3.10c
  autosave track is gated behind its own review gate.
* Module-level statements are limited to imports, constants,
  function defs, and class defs (plus this docstring).
"""
from __future__ import annotations
