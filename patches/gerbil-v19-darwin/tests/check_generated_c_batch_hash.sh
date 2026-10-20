#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned experimental bin required}
output=${2:?fresh owned output required}
case "$bin:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output"
first="$output/space and\\slash"
second="$output/"$'line\nbreak'
printf 'first content\n' > "$first"
printf 'second content\n' > "$second"
paths=("$second" "$first" "$second")
for path in "${paths[@]}"; do
  "$bin/gambit-file-sha256" --raw "$path"
done > "$output/single.log"
"$bin/gambit-file-sha256" --raw-many "${paths[@]}" > "$output/batch.log"
cmp "$output/single.log" "$output/batch.log"
if "$bin/gambit-file-sha256" --raw-many "$first" "$output/missing" > "$output/missing.log" 2>&1; then exit 1; fi
if "$bin/gambit-file-sha256" --raw-many "$output" > "$output/directory.log" 2>&1; then exit 1; fi
if "$bin/gambit-file-sha256" --raw-many > "$output/empty.log" 2>&1; then exit 1; fi
export GAMBIT_GENERATED_C_BATCH_DIGESTS=1
export GENERATION_IMPLEMENTATION="$root/patches/gerbil-v19-darwin/tests/gambit-generated-c-closure.scm"
export GENERATION_FIRST="$first" GENERATION_SECOND="$second" GENERATION_HASH="$bin/gambit-file-sha256"
"$bin/gsc" -e '(load (getenv "GENERATION_IMPLEMENTATION"))' \
  -e '(let* ((paths (list (getenv "GENERATION_SECOND") (getenv "GENERATION_FIRST") (getenv "GENERATION_SECOND"))) (tool (getenv "GENERATION_HASH")))
        (if (not (equal? (generation-file-digests tool paths)
                         (map (lambda (path) (list path (generation-file-sha tool path))) paths)))
            (error "batch decoder order or digest mismatch"))
        (for-each (lambda (bad-tool)
                    (if (not (eq? (with-exception-catcher (lambda (failure) (quote rejected))
                                    (lambda () (generation-file-digests bad-tool paths))) (quote rejected)))
                        (error "batch decoder admitted malformed or failed output" bad-tool)))
                  (list "/usr/bin/true" "/usr/bin/false" "/bin/echo")))' \
  > "$output/decoder.log" 2>&1
printf 'GENERATED-C-BATCH-HASH-OK order duplicates unusual-names missing directory empty decoder-parity decoder-failure\n'
