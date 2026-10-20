#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
home=${1:?owned matching overlaid toolchain required}
output=${2:?fresh owned receipt required}
case "$home:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
export GERBIL_HOME="$home" GERBIL_GSC="$home/bin/gsc" GERBIL_GCC=/opt/homebrew/bin/gcc-16
export GAMBOPT="~~bin=$home/bin,~~lib=$home/lib,~~include=$home/include"
export PATH="$home/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBIT_DARWIN_CLOSED_LINK_REUSE=1 GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
unset CC CFLAGS CPPFLAGS LDFLAGS CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH
unset NIX_CFLAGS_COMPILE NIX_LDFLAGS DEVELOPER_DIR SDKROOT
export LIBRARY_PATH="$(brew --prefix openssl@3)/lib"
printf '(export main)\n(def (main . args) (displayln "CLOSED-DRIVER-SMOKE-OK"))\n' > "$output/entry.ss"
expression="(load \"$home/lib/gerbil/compiler/driver~0.o1\")
 (import :gerbil/compiler)
 (def opts [output-dir: \"$output/lib\" output-file: \"$output/entry\"
            parallel: #t verbose: #t invoke-gsc: #t static: #t])
 (compile-module \"$output/entry.ss\" [invoke-gsc: #f opts ...])
 (compile-exe \"$output/entry.ss\" opts) (execute-pending-compile-jobs!)"
/usr/bin/time -p -o "$output/time.txt" "$home/bin/gxi" -e "$expression" > "$output/build.log" 2>&1
rg -q -- '-closed-c-binding' "$output/build.log"
rg -q '^GAMBIT-CLOSED-LINK-SELECTED ' "$output/build.log"
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' "$output/build.log"
"$output/entry" > "$output/native.stdout"
test "$(cat "$output/native.stdout")" = CLOSED-DRIVER-SMOKE-OK
test ! -e "$output/entry__exe.scm.binding-"
printf 'CLOSED-DRIVER-BUILD-OK real-Gerbil parallel-object-binding native-execution\n'
