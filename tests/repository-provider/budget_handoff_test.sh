#!/usr/bin/env bash
set -euo pipefail

launcher=${1:?generated environment launcher is required}
phase=${2:-caller}
trap 'printf "TOOL-BUDGET-HANDOFF-REFUSED phase=%s\n" "$phase" >&2' ERR

if [[ "$phase" == caller ]]; then
  export GERBIL_BUILD_CORES=1
  export GAMBOPT='max-heap=512M,debug=q,~~=/foreign-runtime,~~bin=/foreign-runtime/bin,~~lib=/foreign-runtime/lib'
  export EXPECTED_CALLER_OPTIONS="$GAMBOPT"
  exec bash "$launcher" bash "$0" "$launcher" admitted
fi

[[ "$GERBIL_BUILD_CORES" == 1 ]]
mappings="~~=$GERBIL_HOME,~~bin=$GERBIL_HOME/bin,~~lib=$GERBIL_HOME/lib"
[[ "$GAMBOPT" == "$EXPECTED_CALLER_OPTIONS,$mappings" ]]

if [[ "$phase" == admitted ]]; then
  export EXPECTED_NESTED_OPTIONS="$GAMBOPT"
  exec bash "$launcher" bash "$0" "$launcher" nested
fi

[[ "$phase" == nested ]]
[[ "$GAMBOPT" == "$EXPECTED_NESTED_OPTIONS" ]]
printf 'TOOL-BUDGET-HANDOFF-OK cores=preserved heap=preserved relocation=bound nested=idempotent\n'
