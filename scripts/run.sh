#!/usr/bin/env bash
#
# Thin wrapper around scripts/executor.py for Linux/macOS servers.
# Finds a dbt-supported python3, then hands off to the Python executor,
# passing through any arguments.
#
# Usage:
#   ./scripts/run.sh                          # full build (run + test)
#   ./scripts/run.sh --command run            # models only
#   ./scripts/run.sh --select tag:ore
#   ./scripts/run.sh --target server --full-refresh
#   ./scripts/run.sh --recreate               # rebuild the venv
#
# All flags are forwarded verbatim to executor.py (see --help there).

set -euo pipefail

# Repo root = parent of this script's directory (works from any CWD).
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# --- Pick a dbt-supported base interpreter (3.9-3.13) --------------------- #
# executor.py builds the venv from this; dbt does NOT support 3.14.
pick_python() {
  local candidates=(python3.11 python3.13 python3.12 python3.10 python3.9 python3 python)
  for c in "${candidates[@]}"; do
    if command -v "$c" >/dev/null 2>&1; then
      # Reject 3.14+ so the venv is created on a supported interpreter.
      if "$c" -c 'import sys; raise SystemExit(0 if (3,9) <= sys.version_info[:2] <= (3,13) else 1)' 2>/dev/null; then
        printf '%s\n' "$c"
        return 0
      fi
    fi
  done
  return 1
}

PY="$(pick_python || true)"
if [[ -z "${PY}" ]]; then
  echo "ERROR: no dbt-supported Python (3.9-3.13) found on PATH." >&2
  echo "       Install one (e.g. python3.11) and retry." >&2
  exit 1
fi

echo "==> Using $PY -> $("$PY" --version 2>&1)"
exec "$PY" scripts/executor.py "$@"
