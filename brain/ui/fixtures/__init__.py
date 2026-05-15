"""Operator TUI fixtures package marker.

Step 6 of the Operator TUI campaign creates this package marker only. The
individual UI fixture modules (``snapshot_view.py``, ``render_view.py``,
``command_router.py``, ``bottom_up_tick.py``, ``tui_smoke.py``) land in
Steps 7-9 and are imported individually by ``brain/invariants.py`` via
``FIXTURE_MODULES`` when they exist.

This module has no runtime side effects on import.
"""
