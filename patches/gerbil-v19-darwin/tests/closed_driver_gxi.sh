#!/usr/bin/env bash
set -euo pipefail
# Qualification only. The published AOT runtime must be rebuilt, not wrapped.
bin=$(cd "$(dirname "$0")" && pwd)
image="$bin/../lib/gerbil/compiler/driver~0.o1"
test -f "$image" && test ! -L "$image"
export GERBIL_QUALIFICATION_DRIVER_IMAGE="$image"
runtime_options=()
while test "$#" -gt 0 && [[ "$1" == -:* ]]; do
  runtime_options+=("$1")
  shift
done
prelude='(import :gerbil/compiler) (load (getenv "GERBIL_QUALIFICATION_DRIVER_IMAGE"))'
if test "${#runtime_options[@]}" -gt 0; then
  set -- "${runtime_options[@]}" interactive -e "$prelude" "$@"
else
  set -- interactive -e "$prelude" "$@"
fi
exec "$bin/gerbil" "$@"
