#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned instrumented diagnostic bin required}
home=${2:?matching runtime home required}
source=${3:?real generated C required}
output=${4:?fresh owned receipt required}
mode=${5:-original}
case "$mode" in original|sanitized) ;; *) exit 2 ;; esac
backend=${6:-shell}
case "$backend" in shell) ;; native) test "$mode" = sanitized ;; *) exit 2 ;; esac
case "$bin:$home:$source:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir "$output"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
cp -p "$source" "$output/probe.c"
cd "$output"
export GERBIL_HOME="$home" GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="$bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
unset GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA GAMBIT_DARWIN_BOUND_SINGLE_PASS
unset GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE GAMBIT_DARWIN_NATIVE_OBJECT_CHECK
unset GAMBIT_DARWIN_BOUND_COLD_CAPTURE GAMBIT_DARWIN_CLOSED_LINK_PRODUCER_PROOF
if test "$backend" = native; then
  export GAMBIT_DARWIN_BOUND_SINGLE_PASS=1 GAMBIT_DARWIN_NATIVE_OBJECT_CAPTURE=1 GAMBIT_DARWIN_NATIVE_OBJECT_CHECK=1
fi
unset CC CFLAGS CPPFLAGS LDFLAGS CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH
unset NIX_CFLAGS_COMPILE NIX_LDFLAGS SDKROOT DEVELOPER_DIR
expected=$("$bin/gambit-file-sha256" --raw "$output/probe.c")
"$bin/gsc" -obj -cc-options "-D___DYNAMIC -fPIC -I $home/lib/static" "$output/probe.c" > ordinary.log 2>&1
test ! -e probe.o.gambit-static-proof
for phase in producer bound-same-mode bound-repeat static-mode static-repeat; do
  if test "$phase" != producer; then
    export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA=${expected%% *}
  fi
  options="-D___DYNAMIC -fPIC -I $home/lib/static"
  case "$phase" in static-*) options="-I $home/lib/static" ;; esac
  "$bin/gsc" -obj -cc-options "$options" "$output/probe.c" > "$phase.log" 2>&1
  cp probe.o "$phase.o"
  cp probe.o.gambit-static-proof "$phase.proof"
  cp probe.o.audit.environment "$phase.environment"
  if test "$backend" = shell; then cp probe.o.audit.context "$phase.context"; fi
done
cmp producer.o bound-same-mode.o
cmp bound-same-mode.o bound-repeat.o
cmp static-mode.o static-repeat.o
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' producer.log
if test "$mode" = sanitized; then
  rg -q '^GAMBIT-STATIC-OBJECT-HIT$' bound-same-mode.log
  cmp producer.environment bound-same-mode.environment
  cmp producer.proof bound-same-mode.proof
else
  rg -q '^GAMBIT-STATIC-OBJECT-MISS$' bound-same-mode.log
fi
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' bound-repeat.log
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' static-mode.log
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' static-repeat.log
if test "$backend" = native; then
  rg -q '^GAMBIT-STATIC-BOUND-NATIVE-CHECK$' bound-same-mode.log
  if cmp -s bound-same-mode.o static-mode.o; then exit 2; fi
else
  test "$(head -n 1 producer.context)" = "$(head -n 1 bound-same-mode.context)"
  if test "$mode" = sanitized; then
    test "$(sed -n '2p' producer.context)" = "$(sed -n '2p' bound-same-mode.context)"
  else
    test "$(sed -n '2p' producer.context)" != "$(sed -n '2p' bound-same-mode.context)"
  fi
  test "$(head -n 1 bound-same-mode.context)" != "$(head -n 1 static-mode.context)"
fi
if test "$mode" = sanitized; then
  export GAMBIT_DARWIN_STATIC_EXPECTED_SOURCE_SHA=0000000000000000000000000000000000000000000000000000000000000000
  status=0
  "$bin/gsc" -obj -cc-options "-I $home/lib/static" "$output/probe.c" > wrong-binding.log 2>&1 || status=$?
  test "$status" != 0
  cmp static-repeat.o probe.o
  printf 'STATIC-PROOF-SANITIZED-OK backend=%s same-recipe-HIT mode-change-MISS wrong-binding-DENY\n' "$backend"
  exit 0
fi
printf 'STATIC-PROOF-BOUNDARY-OK binding-env-only-MISS same-CPP-object mode-change-CPP-MISS repeat-HIT\n'
