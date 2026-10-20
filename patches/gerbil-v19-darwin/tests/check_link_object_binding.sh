#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned bound-input candidate bin required}
output=${2:?fresh owned receipt required}
home=${3:?owned matching toolchain home required}
mode=${4:-ordinary}
link_options=()
case "$mode" in
  ordinary) ;;
  closed-link)
    export GAMBIT_DARWIN_CLOSED_LINK_REUSE=1 GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
    ;;
  *) exit 2 ;;
esac
case "$bin:$output:$home" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test -f "$home/include/gambit.h" && test ! -L "$home/include/gambit.h"
test ! -e "$output"
mkdir -p "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="$bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
cd "$output"
sdk=$(/usr/bin/xcrun --sdk macosx --show-sdk-path)
unset GAMBIT_DARWIN_STATIC_OBJECT_REUSE GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA
printf '(define (link-object-probe) 17)\n' > module.scm
printf '(write (link-object-probe)) (newline)\n' > main.scm
if test "$mode" = closed-link; then link_options=(-closed-c-binding "$PWD/link.binding"); fi
"$bin/gsc" -link "${link_options[@]}" module.scm main.scm > prepare-link.log 2>&1
if test "$mode" = closed-link; then
  rg -q '^GAMBIT-CLOSED-LINK-SELECTED 2$' prepare-link.log
  export CLOSED_BINDING="$PWD/link.binding" CLOSED_BINDING_COUNT=2
  "$bin/gsc" -e "(load \"$root/patches/gerbil-v19-darwin/tests/check_closed_link_manifest.scm\")" > manifest.log 2>&1
  unset CLOSED_BINDING CLOSED_BINDING_COUNT
fi
cp module.c selected.c
expected=$("$bin/gambit-file-sha256" --raw selected.c)
expected=${expected%% *}
"$bin/gsc" -obj module.c main.c main_.c > ordinary-objects.log 2>&1
"$bin/gsc" -exe -cc-options "-isysroot '$sdk'" -o ordinary module.o main.o main_.o > ordinary-link.log 2>&1
./ordinary > ordinary.stdout
test "$(cat ordinary.stdout)" = 17
cp module.o selected.o
printf '(define (link-object-probe) 29)\n' > module.scm
"$bin/gsc" -c module.scm > changed-generation.log 2>&1
"$bin/gsc" -obj module.c > unbound-object.log 2>&1
"$bin/gsc" -exe -cc-options "-isysroot '$sdk'" -o unbound module.o main.o main_.o > unbound-link.log 2>&1
./unbound > unbound.stdout
test "$(cat unbound.stdout)" = 29
cp selected.o module.o
export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA="$expected"
if "$bin/gsc" -obj module.c > bound-rejection.log 2>&1; then exit 1; fi
rg -q '^GAMBIT-STATIC-BOUND-SOURCE-DENY$' bound-rejection.log
cmp selected.o module.o
cp selected.c module.c
rm module.o
"$bin/gsc" -obj module.c > bound-recovery.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' bound-recovery.log
cmp selected.o module.o
unset GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA GAMBIT_DARWIN_STATIC_OBJECT_REUSE
"$bin/gsc" -exe -cc-options "-isysroot '$sdk'" -o bound module.o main.o main_.o > bound-link.log 2>&1
./bound > bound.stdout
cmp ordinary.stdout bound.stdout
printf 'LINK-OBJECT-BINDING-OK actual-Scheme-to-C native-link unbound-29 rejected bound-17\n'
