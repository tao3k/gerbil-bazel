#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?isolated compiler bin required}
output=${2:?fresh output required}
case "$bin:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output/control" "$output/published" "$output/work-first" "$output/work-hit" "$output/work-second"
home=$(cd "$bin/.." && pwd)
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$bin,~~lib=$home/lib,~~include=$home/include"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GENERATION_FIXTURE="$output" GENERATION_BIN="$bin"
export GENERATION_JOURNAL="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-reads.scm"
export GENERATION_IMPLEMENTATION="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-closure.scm"
export GENERATION_CONTRACT="$root/patches/gerbil-v19-darwin/tests/real_generated_c_alias.scm"
"$bin/gsc" -e '(call-with-output-file (string-append (getenv "GENERATION_FIXTURE") "/module.scm") (lambda (port) (display "(define (answer) 17)\n" port)))'
for name in alias-first alias-second; do
  mkdir "$output/control/$name"
  "$bin/gsc" -c -o "$output/control/$name/module.c" -module-ref "$name" -linker-name "$name" -target C "$output/module.scm" > "$output/$name.log" 2>&1
done
"$bin/gsc" -e '(load (getenv "GENERATION_JOURNAL"))' \
  -e '(load (getenv "GENERATION_IMPLEMENTATION"))' \
  -e '(load (getenv "GENERATION_CONTRACT"))' \
  -e '(run-real-generated-c-alias!)' > "$output/output.log" 2>&1
cat "$output/output.log"
rg -q '^REAL-GENERATED-C-ALIAS-OK ' "$output/output.log"
