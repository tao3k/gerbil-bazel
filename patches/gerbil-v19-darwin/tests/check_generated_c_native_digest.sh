#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
bin=${1:?owned matching toolchain bin required}
output=${2:?fresh owned output required}
runtime=${3:?owned matching runtime required}
case "$bin:$output:$runtime" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
mkdir -p "$output"
tests="$root/patches/gerbil-v19-darwin/tests"
cp "$tests/gambit-generated-c-native-digest.scm" "$tests/gambit-file-sha256.c" "$output/"
export GENERATION_NATIVE_DIGEST_MODULE="$output/gambit-generated-c-native-digest.o1"
export GENERATION_IMPLEMENTATION="$tests/gambit-generated-c-closure.scm"
export GENERATION_HASH="$bin/gambit-file-sha256" GENERATION_FIXTURE="$output"
export GAMBIT_GENERATED_C_BATCH_DIGESTS=1
export GAMBOPT="~~bin=$bin,~~lib=$runtime/lib,~~include=$runtime/include"
sdk=$(/usr/bin/xcrun --sdk macosx --show-sdk-path)
"$bin/gsc" -cc-options "-isysroot $sdk -Wno-deprecated-declarations" \
  -ld-options "-Wl,-syslibroot,$sdk -Wl,-undefined,dynamic_lookup -lSystem" \
  -o "$GENERATION_NATIVE_DIGEST_MODULE" "$output/gambit-generated-c-native-digest.scm" \
  > "$output/compile.log" 2>&1
"$bin/gsc" -e '(load (getenv "GENERATION_NATIVE_DIGEST_MODULE"))' \
  -e '(load (getenv "GENERATION_IMPLEMENTATION"))' \
  -e '(define (check condition name) (if (not condition) (error name)) (display name) (newline))
      (let* ((root (getenv "GENERATION_FIXTURE"))
             (tool (getenv "GENERATION_HASH"))
             (file (string-append root "/space and\\slash\nname"))
             (empty (string-append root "/empty")))
        (call-with-output-file file (lambda (port) (display "native digest fixture" port)))
        (call-with-output-file empty (lambda (port) #f))
        (for-each (lambda (path)
                    (check (equal? (generation-native-file-sha path) (generation-file-sha tool path))
                           "NATIVE-DIGEST-PARITY-OK"))
                  (list file empty (getenv "GENERATION_NATIVE_DIGEST_MODULE")))
        (for-each (lambda (path)
                    (check (eq? (with-exception-catcher (lambda (failure) (quote denied))
                                  (lambda () (generation-native-file-sha path))) (quote denied))
                           "NATIVE-DIGEST-FAILURE-OK"))
                  (list root (string-append root "/missing")))
        (let ((before (generation-native-file-sha file)))
          (call-with-output-file file (lambda (port) (display "changed bytes" port)))
          (check (not (equal? before (generation-native-file-sha file))) "NATIVE-DIGEST-MUTATION-OK"))
        (let* ((paths (map (lambda (index) file) (iota 100)))
               (started (time->seconds (current-time)))
               (external (map (lambda (path) (generation-file-sha tool path)) paths))
               (middle (time->seconds (current-time)))
               (native (map generation-native-file-sha paths))
               (ended (time->seconds (current-time))))
          (check (equal? external native) "NATIVE-DIGEST-REPEATED-PARITY-OK")
          (write (list (quote digest-component-seconds) (quote external) (- middle started)
                       (quote native) (- ended middle) (quote calls) 100)) (newline)))' \
  > "$output/controls.log" 2>&1
cat "$output/controls.log"
printf 'GENERATED-C-NATIVE-DIGEST-OK component-only\n'
