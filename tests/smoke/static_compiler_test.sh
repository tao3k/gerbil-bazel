#!/usr/bin/env bash
set -euo pipefail
key=${1:?compiled project runfile key is required}
if [[ -n "${RUNFILES_DIR:-}" ]]; then
  root="$RUNFILES_DIR/$key"
else
  root=$(awk -v key="$key" '$1 == key {sub($1 " ", ""); print; exit}' "$RUNFILES_MANIFEST_FILE")
fi
test -x "$root/.gerbil/bin/main"
test "$("$root/.gerbil/bin/main")" = sdk-static-helper-ok
