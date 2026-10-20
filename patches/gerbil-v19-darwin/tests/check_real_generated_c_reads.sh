#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?isolated compiler bin required}
source=${2:?owned static directory required}
output=${3:?fresh output required}
case "$bin:$source:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output/source" "$output/control" "$output/recorded" "$output/snapshots"
inputs=(); names=()
for path in "$source"/*.scm; do
  test -f "$path" && test ! -L "$path"
  if test ! -f "${path%.scm}.c"; then continue; fi
  name=$(basename "$path")
  cp "$path" "$output/source/$name"
  inputs+=("$output/source/$name")
  names+=("${name%.scm}")
done
test "${#inputs[@]}" -gt 1
home=$(cd "$bin/.." && pwd)
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export READ_PROBE_IMPLEMENTATION="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-reads.scm"
export READ_PROBE_SOURCE="$output/source" READ_PROBE_OUTPUT="$output/recorded"
export READ_PROBE_SCRATCH="$output/snapshots"
cd "$output"
/usr/bin/time -p -o control.time "$bin/gsc" -c -o "$output/control/" \
  "${inputs[@]}" > control.log 2>&1
/usr/bin/time -p -o recorded.time "$bin/gsc" \
  -e '(load (getenv "READ_PROBE_IMPLEMENTATION"))' \
  -e '(record-paired-generated-c-reads! (getenv "READ_PROBE_SOURCE") (getenv "READ_PROBE_OUTPUT") (getenv "READ_PROBE_SCRATCH"))' \
  > recorded.log 2>&1
for name in "${names[@]}"; do
  cmp "$output/control/$name.c" "$output/recorded/$name.c"
  cmp "$output/source/$name.scm" "$output/snapshots/$name/0.source"
  test -s "$output/recorded/$name.c.reads"
done
cat control.time recorded.time recorded.log
printf 'REAL-GENERATED-C-READS-PARITY-OK modules=%s\n' "${#inputs[@]}"
