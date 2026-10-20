#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
original=${1:?owned selected toolchain bin required}
output=${2:?fresh owned receipt required}
home=${3:?owned matching toolchain home required}
expected=${4:?vulnerable or protected required}
object_state=${5:-existing}
mutation_phase=${6:-preprocess}
dispatch=${7:-reuse}
case "$original:$output:$home" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
case "$expected" in vulnerable|protected) ;; *) exit 2 ;; esac
case "$object_state" in existing|missing) ;; *) exit 2 ;; esac
case "$mutation_phase" in preprocess|compile) ;; *) exit 2 ;; esac
case "$dispatch" in reuse|ordinary) ;; *) exit 2 ;; esac
if test "$dispatch" = ordinary && test "$object_state" != missing; then exit 2; fi
test ! -e "$output"
mkdir -p "$output/bin" "$output/work"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
bin="$output/bin"
cp "$original/gambit-static-object-reuse" "$original/gambit-file-sha256" "$bin/"
for tool in gsc gxi gerbil; do ln -s "$original/$tool" "$bin/$tool"; done
# This wrapper changes only the known original input during actual preprocessing.
# All compilation and tool queries still execute the installed genuine GNU GCC.
printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail' \
  'preprocess=0; output=0' \
  'for arg in "$@"; do case "$arg" in -E) if test "$STATIC_SOURCE_ABA_PHASE" = preprocess; then preprocess=1; fi ;; -c) if test "$STATIC_SOURCE_ABA_PHASE:${STATIC_SOURCE_ABA_ARMED-}" = compile:1; then preprocess=1; fi ;; -o) output=1 ;; esac; done' \
  'if test "$preprocess:$output" = 1:1; then' \
  '  cp "$STATIC_SOURCE_ABA_ROOT/source-B.c" "$STATIC_SOURCE_ABA_ROOT/probe.c"' \
  '  printf "source-mutation-triggered\n" >> "$STATIC_SOURCE_ABA_ROOT/mutations.log"' \
  '  trap '\''cp "$STATIC_SOURCE_ABA_ROOT/source-A.c" "$STATIC_SOURCE_ABA_ROOT/probe.c"'\'' EXIT' \
  '  /opt/homebrew/bin/gcc-16 "$@"' \
  'else exec /opt/homebrew/bin/gcc-16 "$@"; fi' > "$bin/compiler"
chmod +x "$bin/compiler"
sed "s|/opt/homebrew/bin/gcc-16|$bin/compiler|g" "$original/gambuild-C" > "$bin/gambuild-C"
chmod +x "$bin/gambuild-C"
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export STATIC_SOURCE_ABA_ROOT="$output/work"
export STATIC_SOURCE_ABA_PHASE=$mutation_phase
cd "$output/work"
printf 'int source_aba_probe(void) { return 17; }\n' > source-A.c
printf 'int source_aba_probe(void) { return 29; }\n' > source-B.c
cp source-A.c probe.c
binding=${GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA-}
binding_present=${GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA+set}
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA
"$bin/gsc" -obj probe.c > control.log 2>&1
cp probe.o control.o
if test "$object_state" = missing; then rm probe.o; fi
export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
export STATIC_SOURCE_ABA_ARMED=1
if test "$binding_present" = set; then export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA="$binding"; fi
"$bin/gsc" -obj probe.c > candidate.log 2>&1
cmp source-A.c probe.c
if test "$dispatch" = ordinary; then
  if rg -q '^GAMBIT-STATIC-OBJECT-(HIT|MISS)$' candidate.log; then exit 2; fi
  test ! -e probe.o.gambit-static-proof
elif test "${GAMBIT_DARWIN_BOUND_COLD_CAPTURE-}" = 1 && test "$object_state" = missing; then
  rg -q '^GAMBIT-STATIC-BOUND-COLD-CAPTURE$' candidate.log
  test ! -e probe.o.gambit-static-proof
else
  rg -q '^GAMBIT-STATIC-OBJECT-MISS$' candidate.log
fi
rg -q '^source-mutation-triggered$' mutations.log
printf 'extern int source_aba_probe(void); int main(void) { return source_aba_probe() == 17 ? 0 : 71; }\n' > main.c
/opt/homebrew/bin/gcc-16 main.c probe.o -o candidate
set +e
./candidate
status=$?
set -e
printf '%s\n' "$status" > semantic-status.txt
if test "$expected" = vulnerable; then
  test "$status" = 71
  if cmp -s control.o probe.o; then exit 1; fi
  printf 'STATIC-SOURCE-ABA-REPRODUCED wrong-object-with-restored-source\n'
else
  test "$status" = 0
  cmp control.o probe.o
  printf 'STATIC-SOURCE-ABA-PROTECTED exact-object-and-runtime-parity\n'
fi
