#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
original=${1:?isolated driver bin required}
output=${2:?fresh output required}
home=${3:-"$root/.data/d1391-runtime-object-source/build"}
case "$original:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
case "$home" in "$root"/.data/*) ;; *) exit 2 ;; esac
if test ! -f "$home/include/gambit.h" || test -L "$home/include/gambit.h"; then exit 2; fi
test ! -e "$output"
mkdir -p "$output/bin" "$output/work"
bin="$output/bin"
cp "$original/gambit-static-object-reuse" "$bin/"
if test -x "$original/gambit-file-sha256"; then cp "$original/gambit-file-sha256" "$bin/"; fi
printf '#!/bin/sh\nexec /opt/homebrew/bin/gcc-16 "$@"\n' > "$bin/compiler"
chmod +x "$bin/compiler"
sed "s|/opt/homebrew/bin/gcc-16|$bin/compiler|g" "$original/gambuild-C" > "$bin/gambuild-C"
chmod +x "$bin/gambuild-C"
for tool in gsc gxi gerbil; do ln -s "$original/$tool" "$bin/$tool"; done
shasum -a 256 "$home/include/gambit.h" "$original/gsc" > "$output/selected-toolchain.sha256"
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
cd "$output/work"
printf 'int safety_probe(void) { return 17; }\n' > probe.c
"$bin/gsc" -obj probe.c > cold.log 2>&1
"$bin/gsc" -obj probe.c > establish.log 2>&1
"$bin/gsc" -obj probe.c > hit.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' hit.log
cp probe.o original.o
printf '\n# Compiler entry-point content mutation.\n' >> "$bin/compiler"
"$bin/gsc" -obj probe.c > compiler-change.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' compiler-change.log
cmp original.o probe.o
"$bin/gsc" -obj probe.c > compiler-repeat.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' compiler-repeat.log
rm probe.o.gambit-static-proof
mkdir probe.o.gambit-static-proof
printf 'foreign-owned-marker\n' > probe.o.gambit-static-proof/marker
if "$bin/gsc" -obj probe.c > proof-directory.log 2>&1; then exit 1; fi
rg -q '^GAMBIT-STATIC-OBJECT-PROOF-DENY$' proof-directory.log
cmp original.o probe.o
test "$(cat probe.o.gambit-static-proof/marker)" = foreign-owned-marker
test "$(ls -A probe.o.gambit-static-proof | wc -l | tr -d ' ')" = 1
rm probe.o.gambit-static-proof/marker
rmdir probe.o.gambit-static-proof
printf 'foreign-proof\n' > foreign-proof
ln -s foreign-proof probe.o.gambit-static-proof
if "$bin/gsc" -obj probe.c > proof-symlink.log 2>&1; then exit 1; fi
rg -q '^GAMBIT-STATIC-OBJECT-PROOF-DENY$' proof-symlink.log
cmp original.o probe.o
test "$(cat foreign-proof)" = foreign-proof
test -L probe.o.gambit-static-proof
rm probe.o.gambit-static-proof
printf 'int warning_probe(void) { int unused; return 17; }\n' > warning.c
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE
"$bin/gsc" -obj -cc-options '-Wall -Wunused-variable' warning.c > warning-control.log 2>&1
cp warning.o warning-control.o
export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
for round in first repeat; do
  "$bin/gsc" -obj -cc-options '-Wall -Wunused-variable' warning.c > "warning-$round.log" 2>&1
  cmp warning-control.log "warning-$round.log"
  cmp warning-control.o warning.o
  test ! -e warning.o.gambit-static-proof
done
rg -q 'warning:' warning-control.log
printf '%s\n' '#!/bin/sh' \
  'for argument do' \
  '  case "$argument" in *.i)' \
  '    if test "${STATIC_REUSE_MUTATION_MODE-}" = 1; then' \
  '      : > "${STATIC_REUSE_MUTATION_SIGNAL}.ready"' \
  '      attempts=0' \
  '      while test ! -f "${STATIC_REUSE_MUTATION_SIGNAL}.release"; do' \
  '        attempts=$((attempts+1))' \
  '        test "$attempts" -lt 1000 || exit 2' \
  '        sleep .01' \
  '      done' \
  '    fi ;; esac' \
  'done' \
  'exec /opt/homebrew/bin/gcc-16 "$@"' > "$bin/compiler"
export STATIC_REUSE_MUTATION_SIGNAL="$PWD/mutation"
"$bin/gsc" -obj probe.c > mutation-establish.log 2>&1
cp probe.o before-mutation.o
cp probe.o.gambit-static-proof before-mutation.proof
export STATIC_REUSE_MUTATION_MODE=1
for mutation in compiler source; do
  rm -f mutation.ready mutation.release
  printf 'int safety_probe(void) { return 29; }\n' > probe.c
  "$bin/gsc" -obj probe.c > "mutation-$mutation.log" 2>&1 &
  child=$!
  trap 'kill "$child" 2>/dev/null || true; wait "$child" 2>/dev/null || true' EXIT
  attempts=0
  while test ! -f mutation.ready; do
    attempts=$((attempts+1))
    test "$attempts" -lt 1000 || exit 2
    sleep .01
  done
  if test "$mutation" = compiler; then
    printf '\n# Mid-flight compiler entry-point mutation.\n' >> "$bin/compiler"
  else
    printf 'int safety_probe(void) { return 37; }\n' > probe.c
  fi
  : > mutation.release
  if wait "$child"; then exit 1; fi
  trap - EXIT
  cmp before-mutation.o probe.o
  cmp before-mutation.proof probe.o.gambit-static-proof
  if rg -q '^GAMBIT-STATIC-OBJECT-(HIT|MISS)$' "mutation-$mutation.log"; then exit 1; fi
done
test ! -d probe.o.gambit-static-lock
test ! -d warning.o.gambit-static-lock
printf 'STATIC-OBJECT-SAFETY-OK 6\n'
