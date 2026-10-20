#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?isolated adapter bin required}
output=${2:?fresh output required}
case "$bin:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output/control" "$output/published" "$output/fallback"
export PATH="/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export GAMBOPT="~~bin=$bin,~~lib=$bin/../lib,~~include=$bin/../include"
export GAMBIT_DARWIN_GENERATED_C_REUSE=1
export GENERATION_FIXTURE="$output"
"$bin/gsc-original" -e '(call-with-output-file (string-append (getenv "GENERATION_FIXTURE") "/module.scm") (lambda (port) (display "(define (answer) 17)\n" port)))'
"$bin/gsc-original" -c -o "$output/control/module.c" -module-ref producer-alias -linker-name producer-alias "$output/module.scm"
"$bin/gsc" -c -o "$output/published/module.c" -module-ref producer-alias -linker-name producer-alias "$output/module.scm" > "$output/first.log" 2>&1
cmp "$output/control/module.c" "$output/published/module.c"
"$bin/gsc" -c -o "$output/published/module.c" -module-ref producer-alias -linker-name producer-alias "$output/module.scm" > "$output/repeat.log" 2>&1
rg -q '^GAMBIT-GENERATED-C-MISS$' "$output/first.log"
rg -q '^GAMBIT-GENERATED-C-HIT$' "$output/repeat.log"
"$bin/gsc-original" -c -o "$output/control/module.c" -module-ref changed-alias -linker-name changed-alias "$output/module.scm"
"$bin/gsc" -c -o "$output/published/module.c" -module-ref changed-alias -linker-name changed-alias "$output/module.scm" > "$output/alias-change.log" 2>&1
rg -q '^GAMBIT-GENERATED-C-MISS$' "$output/alias-change.log"
cmp "$output/control/module.c" "$output/published/module.c"
"$bin/gsc-original" -e '(call-with-output-file (list path: (string-append (getenv "GENERATION_FIXTURE") "/module.scm") truncate: #t) (lambda (port) (display "(define (answer) 29)\n" port)))'
"$bin/gsc-original" -c -o "$output/control/module.c" -module-ref changed-alias -linker-name changed-alias "$output/module.scm"
"$bin/gsc" -c -o "$output/published/module.c" -module-ref changed-alias -linker-name changed-alias "$output/module.scm" > "$output/source-change.log" 2>&1
rg -q '^GAMBIT-GENERATED-C-MISS$' "$output/source-change.log"
cmp "$output/control/module.c" "$output/published/module.c"
cp "$output/published/module.c.generation-proof" "$output/saved-proof"
"$bin/gsc-original" -e '(call-with-output-file (list path: (string-append (getenv "GENERATION_FIXTURE") "/module.scm") truncate: #t) (lambda (port) (display "(define (answer)\n" port)))'
if "$bin/gsc" -c -o "$output/published/module.c" -module-ref changed-alias -linker-name changed-alias "$output/module.scm" > "$output/failure.log" 2>&1; then
  exit 1
fi
cmp "$output/control/module.c" "$output/published/module.c"
cmp "$output/saved-proof" "$output/published/module.c.generation-proof"
"$bin/gsc-original" -e '(call-with-output-file (list path: (string-append (getenv "GENERATION_FIXTURE") "/module.scm") truncate: #t) (lambda (port) (display "(define (answer) 29)\n" port)))'
"$bin/gsc" -c -o "$output/fallback/module.c" "$output/module.scm" > "$output/fallback.log" 2>&1
! rg -q 'GAMBIT-GENERATED-C-' "$output/fallback.log"
test ! -e "$output/fallback/module.c.generation-proof"
test ! -e "$output/published/module.c.generation-proof.lock"
test -z "$(fd -H -d 1 'gambit-generation-(request|work)' "$output/published")"
printf 'GENERATED-C-DISPATCH-OK original-parity cross-process-hit alias-invalidation source-invalidation failure-preservation fallback cleanup\n'
