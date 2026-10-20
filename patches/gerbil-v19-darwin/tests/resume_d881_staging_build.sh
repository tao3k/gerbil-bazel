#!/bin/sh
set -eu
source_root=${1:?source checkout required}
scripts=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
unset SDKROOT DEVELOPER_DIR CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH LIBRARY_PATH LDFLAGS PKG_CONFIG_PATH
host_environment=$(python3 "$scripts/bazel_host_environment.py")
eval "$host_environment"
GNU_GCC=$GERBIL_GNU_GCC
export GERBIL_GCC="$scripts/gambit-gnu-gcc.sh"
cd "$source_root"
case ${2:-} in
  --skip-gambit) test -x src/gambit/gsc/gsc && test -f src/gambit/lib/libgambit.a ;;
  "") make -C src/gambit -j2 \
        "C_COMPILER=$GNU_GCC -ftrack-macro-expansion=0" from-scratch ;;
  *) printf 'Unknown option: %s\n' "$2" >&2; exit 1 ;;
esac

# Same installation boundary as src/build.sh:build_gambit, without clearing
# the completed bootstrap objects to reenter that function.
cp src/gambit/gsi/gsi bootstrap/bin/
cp src/gambit/gsc/gsc src/gambit/bin/gambuild-C build/bin/
cp src/gambit/include/gambit.h src/gambit/include/gambit-not*.h build/include/
cp src/gambit/lib/*\#.scm src/gambit/lib/_define-syntax.scm build/lib/
cp src/gambit/gsc/*\#.scm src/gambit/lib/_gambit.c build/lib/
for file in lib/libgambit.a gsi/libgambitgsi.a gsc/libgambitgsc.a; do
  cp "src/gambit/$file" build/lib/
done
for stage in boot-gxi stage0 stage1 stdlib libgerbil lang tools; do
  printf '\nD882-STAGE %s\n' "$stage"
  ./build.sh "$stage"
done
