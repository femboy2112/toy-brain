#!/usr/bin/env bash
# Run every consistency check in one shot:
#   0. brain/_catalog_ids.py is in sync with INVARIANT_CATALOG.md.
#   1. Catalog summary counts (banner vs parsed vs expected; strict gate).
#   2. Lean citation resolution against lean_reference/.
#   3. I-PCE-05 import audit (agency.py free of pce imports).
#   4. Full invariant runner (includes I-CAT-01 coverage audit).
# Exits non-zero on the first failure.

set -euo pipefail

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${THIS_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

step() { printf "\n=== %s ===\n" "$*"; }

step "0/5 generated catalog IDs freshness"
python -m tools.catalog generate-ids
if ! git diff --quiet brain/_catalog_ids.py; then
  printf "\nERROR: brain/_catalog_ids.py is stale.\n"
  printf "Run 'python -m tools.catalog generate-ids' and commit the result.\n"
  exit 1
fi

step "1/5 catalog counts (strict)"
python -m tools.catalog counts

step "2/5 citation verification"
python -m tools.citations verify

step "3/5 import audit (I-PCE-05)"
python -m tools.import_audit

step "4/5 invariant runner (includes I-CAT-01)"
python -m brain.invariants run

printf "\nAll checks passed.\n"
