#!/usr/bin/env bash
# Convenience wrapper around `python3 -m brain.invariants run`.
# Forwards every argument; default mode is strict (non-zero exit on any red).

set -euo pipefail

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${THIS_DIR}/.." && pwd)"

cd "${REPO_ROOT}"
python3 -m brain.invariants run "$@"
