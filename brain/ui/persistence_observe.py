"""Phase 3.10b Persistence Observability — placeholder.

This module is the Step 7 catalog-patch placeholder for Phase 3.10b
of the Operational Hardening + Persistence Observability + Autosave
campaign. It declares the hard boundaries the Step 9 implementation
must respect. No runtime is wired here yet; the observability
helpers (``db_summary``, ``profile_summary``, ``stream_db_summary``,
``db_diff``) and the typed report records (``DbSummaryReport``,
``ProfileSummaryReport``, ``ProfileSummaryRow``,
``StreamDbSummaryReport``, ``StreamDbSummaryRow``, ``DbDiffField``,
``DbDiffReport``) land in Step 9.

Hard boundaries pinned by
``PHASE3_10_OPERATIONAL_OBSERVABILITY_AUTOSAVE_CORRIGENDA.md`` and
``PHASE3_10_OPS_OBSERVABILITY_CATALOG_PATCH_PLAN.md``:

* SQLite via the standard-library ``sqlite3`` module only — no
  ``pickle`` / ``shelve`` / ``marshal`` / ``dill`` / ``cloudpickle``
  / ``joblib`` / ``subprocess`` / ``socket`` / ``urllib`` / ``http``
  / ``requests`` / ``curses`` / ``brain.tick`` / ``brain.tlica``
  internals beyond what ``brain.ui.persistence`` re-exports /
  ``brain.llm``.
* Every helper opens the DB through
  ``sqlite3.connect("file:<path>?mode=ro", uri=True)`` inside a
  ``with conn:`` block.
* No helper invokes any kernel builder
  (``make_profile_with_cogito``, ``make_msi``, ``make_ptcns``,
  ``ContentRegistry``, ``BrainState``, ``make_text_stream_chunk``,
  ``TextStreamHistory``, ``make_stream_promotion_candidate``,
  ``OperatorSession``); no helper mutates ``session.state`` /
  ``session.stream_history`` / ``session.stream_candidates`` /
  ``session.tick_counter`` / ``session.stream_chunk_serial``.
* All ``Fraction`` values display as exact ``"num/den"`` strings via
  a single shared render helper; no ``float()`` / ``repr()`` / JSON
  leakage.
* ``db_diff`` reuses the public ``snapshot_session`` helper promoted
  from ``brain.ui.persistence`` (Phase 3.10b narrow extension) to
  project the live session and ``_deserialize_from_db`` to read the
  saved snapshot; the diff is over the finite field enumeration
  declared in source and uses the literal ``"<missing>"`` for
  one-sided absence (never a silent ``0`` or ``null``).
* The four typed verbs route through ``OperatorSession.dispatch``
  with new ``OperatorCommand`` kinds (``DB_SUMMARY``,
  ``PROFILE_SUMMARY``, ``STREAM_DB_SUMMARY``, ``DB_DIFF``); none
  of them calls ``tick()`` or opens curses; none of them stores a
  ``sqlite3.Connection`` on ``OperatorSession``.
* Locked default row caps: ``PROFILE_SUMMARY_ROW_CAP = 64``,
  ``STREAM_DB_SUMMARY_HEAD_CAP = 8``,
  ``STREAM_DB_SUMMARY_TAIL_CAP = 8``, ``DB_DIFF_ROW_CAP = 32``,
  ``STREAM_TEXT_PREVIEW_MAX_LEN = 64``,
  ``OPS_REPORT_TEXT_MAX_LEN = 256``,
  ``PROFILE_VALUE_STRING_MAX_LEN = 64``.
* Phase 3.10b adds NO new ``OperatorSession`` field.
* No autosave entry point exists; no ``@atexit`` / signal /
  threading / asyncio autosave hook is registered.
* Module-level statements are limited to imports, constants,
  function defs, and class defs (plus this docstring).
"""
from __future__ import annotations
