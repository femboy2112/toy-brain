#!/usr/bin/env bash
# Run every consistency check in one shot:
#   1. Catalog summary counts (banner vs parsed vs expected).
#   2. Lean citation resolution against lean_reference/.
#   3. I-PCE-05 import audit (agency.py free of pce imports).
#   4. Full invariant runner.
# Exits non-zero on the first failure.

set -euo pipefail

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${THIS_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

step() { printf "\n=== %s ===\n" "$*"; }

step "1/4 catalog counts"
python -m tools.catalog counts

step "2/4 citation verification"
python -m tools.citations verify

step "3/4 import audit (I-PCE-05)"
python -m tools.import_audit

step "4/4 invariant runner"
python -m brain.invariants run

printf "\nAll checks passed.\n"
