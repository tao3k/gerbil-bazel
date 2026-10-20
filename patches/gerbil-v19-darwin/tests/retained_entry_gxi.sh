#!/usr/bin/env bash
set -euo pipefail
: "${GERBIL_HOME:?selected installed profile required}"
: "${GAMBIT_DARWIN_DRIVER_OVERLAY:?selected compiled overlay required}"
test -f "$GAMBIT_DARWIN_DRIVER_OVERLAY" && test ! -L "$GAMBIT_DARWIN_DRIVER_OVERLAY"
runtime_options=()
while test "$#" -gt 0; do
  case "$1" in -:*) runtime_options+=("$1"); shift ;; *) break ;; esac
done
exec "$GERBIL_HOME/bin/gxi" \
  "${runtime_options[@]}" \
  -e '(import :gerbil/compiler) (load (getenv "GAMBIT_DARWIN_DRIVER_OVERLAY"))' "$@"
