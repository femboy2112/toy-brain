"""Operator TUI package marker (Step 6 of the Operator TUI campaign).

The Operator TUI is an operator-facing terminal interface that inspects
``BrainState`` / ``TickRecord`` / Phase 3.1-3.4 developmental histories and
routes bottom-up ``PerceptEvent`` inputs through the existing public
``tick()`` entrypoint. It is not a cognitive layer.

Step 6 of ``CURRENT_CAMPAIGN.md`` introduces only this package marker plus
``brain/ui/fixtures/__init__.py``; runtime UI modules (``snapshot.py``,
``render.py``, ``commands.py``, ``session.py``, ``tui.py``, ``__main__.py``)
land in Step 7 (snapshots + renderer), Step 8 (commands + session +
bottom-up event path), and Step 9 (curses wrapper + entrypoint + UI import
audit). Until then the catalog rows ``I-UI-01..13`` are registered as
NotImplementedError-failing pending checks inside ``brain/invariants.py`` so
that ``I-CAT-01`` coverage stays coherent.

This module deliberately does not import ``curses``, ``brain.tick``,
``brain.tlica``, or ``brain.llm``. It has no runtime side effects on
import.
"""
