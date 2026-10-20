#!/bin/sh
set -eu
source_root=${1:?source checkout required}
scripts=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
unset SDKROOT DEVELOPER_DIR CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH LIBRARY_PATH LDFLAGS PKG_CONFIG_PATH
host_environment=$(python3 "$scripts/bazel_host_environment.py")
eval "$host_environment"
export GERBIL_GCC="$scripts/gambit-gnu-gcc.sh"
start_stage=${2:-stdlib}
cd "$source_root"
started=false
for stage in stage1-bach stdlib libgerbil lang tools; do
  if [ "$stage" = "$start_stage" ]; then started=true; fi
  if [ "$started" = false ]; then continue; fi
  printf '\nD882-STAGE %s\n' "$stage"
  ./build.sh "$stage"
  printf 'D882-STAGE-OK %s\n' "$stage"
done
[ "$started" = true ] || { printf 'Unknown stage: %s\n' "$start_stage" >&2; exit 1; }
