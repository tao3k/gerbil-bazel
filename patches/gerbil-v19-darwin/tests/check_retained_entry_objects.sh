#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
driver=${1:?selected frozen driver bin required}
home=${2:?selected toolchain required}
output=${3:?fresh owned receipt required}
case "$driver:$home:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
test -f "$driver/gambit-static-object-reuse" && test ! -L "$driver/gambit-static-object-reuse"
mkdir -p "$output/work"
trap 'status=$?; printf "%s\n" "$status" > "$output/exit-status.txt"' EXIT
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$driver,~~lib=$home/lib,~~include=$home/include"
export GAMBIT_DARWIN_STATIC_OBJECT_REUSE=1
cp "$root/patches/gerbil-v19-darwin/tests/retained_entry_probe.scm" "$output/work/entry.scm"
cd "$output/work"
"$driver/gsc" -link -o closure.c entry.scm > generate-first.log 2>&1
for source in entry.c closure.c; do
  test -f "$source"
  cp "$source" "$source.reference"
  "$driver/gsc" -obj "$source" > "$source.cold.log" 2>&1
  /usr/bin/time -p -o "$source.populate.time" "$driver/gsc" -obj "$source" > "$source.populate.log" 2>&1
  cp "${source%.c}.o" "$source.object-reference"
done
"$driver/gsc" -link -o closure.c entry.scm > generate-repeat.log 2>&1
for source in entry.c closure.c; do
  cmp "$source.reference" "$source"
  /usr/bin/time -p -o "$source.hit.time" "$driver/gsc" -obj "$source" > "$source.hit.log" 2>&1
  rg -q '^GAMBIT-STATIC-OBJECT-HIT$' "$source.hit.log"
  cmp "$source.object-reference" "${source%.c}.o"
done
"$driver/gsc" -obj entry.c > concurrent-a.log 2>&1 &
first=$!
"$driver/gsc" -obj entry.c > concurrent-b.log 2>&1 &
second=$!
wait "$first"
wait "$second"
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' concurrent-a.log
rg -q '^GAMBIT-STATIC-OBJECT-HIT$' concurrent-b.log
cmp entry.c.object-reference entry.o
# Actual executable generation/linking must retain the same program behavior.
"$driver/gsc" -exe -o native-entry entry.scm > executable.log 2>&1
./native-entry > native.stdout
test "$(cat native.stdout)" = 17
# GSC's executable path cleans intermediates; re-establish an existing-object
# proof before testing source invalidation rather than mistaking cold fallback.
"$driver/gsc" -link -o closure.c entry.scm > regenerate-after-exe.log 2>&1
"$driver/gsc" -obj entry.c > restore-cold.log 2>&1
"$driver/gsc" -obj entry.c > restore-proof.log 2>&1
test -f entry.o.gambit-static-proof
cp "$root/patches/gerbil-v19-darwin/tests/retained_entry_changed_probe.scm" entry.scm
"$driver/gsc" -link -o closure.c entry.scm > generate-changed.log 2>&1
if cmp -s entry.c.reference entry.c; then exit 1; fi
"$driver/gsc" -obj entry.c > changed.log 2>&1
rg -q '^GAMBIT-STATIC-OBJECT-MISS$' changed.log
cp entry.o changed.o
GAMBIT_DARWIN_STATIC_OBJECT_REUSE=0 "$driver/gsc" -obj entry.c > changed-reference.log 2>&1
cmp changed.o entry.o
"$driver/gsc" -exe -o native-entry entry.scm > changed-executable.log 2>&1
./native-entry > changed-native.stdout
test "$(cat changed-native.stdout)" = 42
printf 'RETAINED-ENTRY-OBJECTS-OK regenerated-C-parity two-object-HITs concurrent-HITs source-change-MISS ordinary-object-parity native-values-17-and-42\n'
