"""CLI wrapper around brain._import_audit.

The audit logic lives inside brain/ to keep tools/ a developer-only directory.

CLI:
    python -m tools.import_audit
"""
from __future__ import annotations

import sys

from brain._import_audit import audit_agency_no_pce_import


def main() -> int:
    ok, msg = audit_agency_no_pce_import()
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
