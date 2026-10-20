#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned configured request driver bin required}
home=${2:?matching toolchain home required}
source=${3:?real generated C required}
output=${4:?fresh owned receipt required}
case "$bin:$home:$source:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
cp -p "$source" "$output/probe.c"
export PATH="$bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GERBIL_HOME="$home" GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export GAMBIT_DARWIN_NATIVE_OBJECT_BATCH=1 GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE=1
export GAMBIT_DARWIN_NATIVE_OBJECT_CHECK=1 GAMBIT_DARWIN_BOUND_SINGLE_PASS=1
unset GAMBIT_DARWIN_OBJECT_PREPARE_DIRECTORY GAMBIT_DARWIN_STATIC_OBJECT_REUSE
unset CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH NIX_CFLAGS_COMPILE NIX_LDFLAGS
unset CC CFLAGS CPPFLAGS LDFLAGS SDKROOT DEVELOPER_DIR GCC_COMPARE_DEBUG
cd "$output"
export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA=$("$bin/gambit-file-sha256" --raw "$output/probe.c")
"$bin/gsc" -obj -cc-options '-D___DYNAMIC -fPIC' "$output/probe.c" > ordinary.log 2>&1
cp probe.o ordinary.o
cp probe.o.gambit-static-proof ordinary.proof
env GAMBIT_DARWIN_OBJECT_PREPARE_DIRECTORY="$output/prepared" \
  "$bin/gsc" -obj -cc-options '-D___DYNAMIC -fPIC' "$output/probe.c" > prepared.log 2>&1
cmp ordinary.o probe.o
cmp ordinary.proof probe.o.gambit-static-proof
rg -q '^GAMBIT-STATIC-OBJECT-REQUEST-PREPARED$' prepared.log
if rg -q '^GAMBIT-STATIC-(OBJECT-(HIT|MISS)|BOUND-NATIVE-CAPTURE)$' prepared.log; then exit 1; fi
printf '%s\000' gambit-native-object-batch-v3 > request
cat prepared/record >> request
"$bin/gambit-file-sha256" --batch "$output/request" "$output/stage" 1 > batch.log 2>&1
cmp ordinary.o probe.o
cmp ordinary.proof probe.o.gambit-static-proof
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' batch.log
rg -q '^GAMBIT-STATIC-OBJECT-BATCH-COMMIT$' batch.log
shasum -a 256 probe.c ordinary.o ordinary.proof "$bin/gsc" "$bin/gambuild-C" \
  "$bin/gambit-object-request-prepare" "$bin/gambit-file-sha256" > identity.log
printf 'OBJECT-REQUEST-DRIVER-OK actual-GSC configured-metadata no-prepare-publication existing-proof-HIT exact-object-proof-parity\n'
