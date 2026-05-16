"""Phase 3.10c Autosave Policy — placeholder.

This module is the Step 17 catalog-patch placeholder for Phase 3.10c
of the Operational Hardening + Persistence Observability + Autosave
campaign. It declares the hard boundaries the Step 18 implementation
must respect. No runtime is wired here yet; the autosave helpers
(``autosave_status``, ``autosave_enable``, ``autosave_disable``,
``maybe_autosave_after_mutation``), the typed report records
(``AutosaveConfig``, ``AutosaveStatusReport``), and the closed enums
(``AutosaveMode``, ``AutosaveTrigger``) land in Step 18.

Hard boundaries pinned by
``PHASE3_10C_AUTOSAVE_CORRIGENDA.md`` and
``PHASE3_10C_AUTOSAVE_CATALOG_PATCH_PLAN.md``:

* ``AutosaveMode`` is a finite closed ``(str, Enum)`` with exactly
  ``OFF`` and ``AFTER_SUCCESSFUL_MUTATION`` members
  (``SUPPORTED_AUTOSAVE_MODES``).
* ``AutosaveTrigger`` is a finite closed ``(str, Enum)`` with exactly
  ``STEP_TICK`` and ``STREAM_PROMOTE`` members
  (``SUPPORTED_AUTOSAVE_TRIGGERS``).
* The default is ``OFF`` on every cold start at session construction
  AND at CLI parse time; no ambient environment variable widens the
  runtime surface (no ``BRAIN_AUTOSAVE_MODE``).
* ``AutosaveConfig`` with mode != ``OFF`` and empty ``db_path_str``
  raises ``ValueError``.
* ``/autosave-enable`` requires a configured ``--session-db``; it
  raises ``PersistenceError`` when ``session.session_store_config``
  is ``None``.
* ``/autosave-disable`` is idempotent and never raises.
* ``/autosave-status`` returns a bounded ``AutosaveStatusReport``
  and never raises.
* ``maybe_autosave_after_mutation`` is the SOLE autosave entry
  point reachable from any dispatch path; it fires AFTER
  ``OperatorSession.dispatch`` returns from a successful mutating
  dispatch (``/step`` with ``STEP_TICK``, ``/stream-promote`` with
  ``STREAM_PROMOTE``); it never fires after a failed dispatch,
  never fires after a read-only dispatch, and never fires inside
  ``tick()``. It absorbs every ``PersistenceError`` into the typed
  status report and NEVER raises.
* Autosave reuses the Phase 3.9 ``save_session`` helper via the
  existing transactional ``BEGIN IMMEDIATE`` / ``COMMIT`` /
  ``ROLLBACK`` discipline; there is no second save code path.
* Failure preserves the live ``OperatorSession`` and the on-disk
  session DB.
* SQLite via the standard-library ``sqlite3`` module only (and only
  through the reused ``save_session`` helper) — this module imports
  no ``pickle`` / ``shelve`` / ``marshal`` / ``dill`` / ``cloudpickle``
  / ``joblib`` / ``subprocess`` / ``socket`` / ``urllib`` / ``http``
  / ``requests`` / ``curses`` / ``brain.tick`` / ``brain.tlica``
  internals beyond what ``brain.ui.persistence`` re-exports /
  ``brain.llm``.
* No ``@atexit.register``, no ``threading``, no ``asyncio``, no
  signal handler, no ``curses`` callback, no ``tick(`` call.
* ``OperatorSession`` carries two new optional fields
  (``autosave_config: Optional[AutosaveConfig]``,
  ``last_autosave_status: Optional[AutosaveStatusReport]``);
  ``_ALLOWED_SESSION_ATTRS`` is extended with both names; neither
  field carries a ``sqlite3.Connection``, ``Cursor``, callable,
  socket, subprocess handle, file object, curses object, or LLM
  client.
* The outcome-detection contract pins ``_dispatch_step_tick`` and
  ``_dispatch_stream_promote`` to return ``Optional[bool]`` so the
  central dispatch reads the mutation outcome without scanning
  status strings.
* Module-level statements are limited to imports, constants,
  function defs, and class defs (plus this docstring).
"""
from __future__ import annotations
