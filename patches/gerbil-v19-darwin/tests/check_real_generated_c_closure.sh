#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?isolated compiler bin required}
source=${2:?owned static directory required}
output=${3:?fresh output required}
runtime=${4:?matching isolated compiler runtime required}
policy=${5:-original}
case "$policy" in original|snapshot) ;; *) exit 2 ;; esac
case "$bin:$source:$output:$runtime" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
cmp "$bin/gsc" "$runtime/bin/gsc"
test -f "$runtime/lib/_gambit.c"
test -d "$runtime/include"
test ! -e "$output"
mkdir -p "$output/source" "$output/control" "$output/published" "$output/work-first" "$output/work-second"
inputs=(); names=()
for path in "$source"/*.scm; do
  test -f "$path" && test ! -L "$path"
  if test ! -f "${path%.scm}.c"; then continue; fi
  name=$(basename "$path")
  cp "$path" "$output/source/$name"
  inputs+=("$output/source/$name")
  names+=("${name%.scm}")
done
test "${#inputs[@]}" = 55
printf '%s\n' "${inputs[@]}" > "$output/ordered-inputs.txt"
home=$(cd "$bin/.." && pwd)
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$runtime/lib,~~include=$runtime/include"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GENERATION_FIXTURE="$output" GENERATION_BIN="$bin"
export GENERATION_JOURNAL="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-reads.scm"
export GENERATION_IMPLEMENTATION="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-closure.scm"
export GENERATION_CONTRACT="$root/patches/gerbil-v19-darwin/tests/real_generated_c_closure.scm"
extra=()
if test "$policy" = snapshot; then
  export GENERATION_SNAPSHOT_JOURNAL="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-snapshot-reads.scm"
  extra=(-e '(load (getenv "GENERATION_SNAPSHOT_JOURNAL"))')
fi
cd "$output"
/usr/bin/time -p -o control.time "$bin/gsc" -c -target C -o "$output/control/" "${inputs[@]}" > control.log 2>&1
"$bin/gsc" -e '(load (getenv "GENERATION_JOURNAL"))' \
  "${extra[@]}" \
  -e '(load (getenv "GENERATION_IMPLEMENTATION"))' \
  -e '(load (getenv "GENERATION_CONTRACT"))' \
  -e '(run-real-generated-c-closure!)' > output.log 2>&1
canonical=(); pinned=()
for name in "${names[@]}"; do
  cmp "$output/control/$name.c" "$output/published/$name.c"
  canonical+=("$output/published/$name.c")
done
while IFS= read -r path; do
  case "$path" in "$output"/.gambit-c-*/*.c) ;; *) exit 2 ;; esac
  test -f "$path" && test ! -L "$path"
  pinned+=("$path")
done < "$output/pinned-inputs.txt"
test "${#pinned[@]}" = "${#canonical[@]}"
"$bin/gsc" -link -target C -o "$output/closure.c" "${canonical[@]}" > link-control.log 2>&1
cp "$output/closure.c" "$output/control-closure.c"
"$bin/gsc" -link -target C -o "$output/closure.c" "${pinned[@]}" > link-pinned.log 2>&1
cmp "$output/control-closure.c" "$output/closure.c"
cat control.time output.log
rg -q '^REAL-GENERATED-C-CLOSURE-OK 55$' output.log
printf 'REAL-GENERATED-C-PINNED-LINK-OK 55\n'
