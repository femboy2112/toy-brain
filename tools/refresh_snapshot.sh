#!/usr/bin/env bash
# Refresh-snapshot workflow per SPEC_UPDATES.md.
#
# Clones (or fetches) github.com/femboy2112/lean-scratch into a /tmp scratch
# directory, then prints a structured diff against the local lean_reference/
# snapshot. Does NOT overwrite lean_reference/; that is a deliberate manual
# step gated on catalog review.

set -euo pipefail

REPO_URL="${LEAN_SCRATCH_URL:-https://github.com/femboy2112/lean-scratch}"
SCRATCH="${LEAN_SCRATCH_DIR:-/tmp/lean-scratch-latest}"
THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${THIS_DIR}/.." && pwd)"

if [[ -d "${SCRATCH}/.git" ]]; then
  echo ">>> Fetching upstream into ${SCRATCH}"
  git -C "${SCRATCH}" fetch origin
  git -C "${SCRATCH}" checkout origin/main 2>/dev/null || git -C "${SCRATCH}" checkout origin/master
else
  echo ">>> Cloning ${REPO_URL} into ${SCRATCH}"
  rm -rf "${SCRATCH}"
  git clone --depth 1 "${REPO_URL}" "${SCRATCH}"
fi

echo
echo ">>> Catalog vs. upstream declaration diff"
cd "${REPO_ROOT}"
python -m tools.snapshot_diff "${SCRATCH}" || true

echo
echo ">>> Catalog citations still resolving against the LOCAL snapshot"
python -m tools.citations verify || true

echo
echo "To accept the upstream snapshot, follow SPEC_UPDATES.md §8 manually:"
echo "  rm -rf lean_reference/TLICA && cp -r ${SCRATCH}/TLICA lean_reference/TLICA"
echo "  cp ${SCRATCH}/TLICA.lean lean_reference/TLICA.lean"
echo "Then update INVARIANT_CATALOG.md and re-run tools/check_all.sh."
