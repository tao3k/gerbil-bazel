#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
runtime=${1:?owned matching runtime required}
native=${2:?owned matching native GSC bin required}
output=${3:?fresh owned output required}
interpreter=${5:-$runtime/bin/gerbil}
case "$runtime:$native:$output" in "$root"/.data/*:"$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
case "$interpreter" in "$root"/.data/*) ;; *) exit 2 ;; esac
test -f "$interpreter"
test ! -e "$output"
patch=0022-gerbil-darwin-opt-in-library-static-capture.patch
case "${4:-all-producers}" in
  all-producers) ;;
  planned-producers) patch=0023-gerbil-darwin-planned-library-producer.patch ;;
  *) exit 2 ;;
esac
mkdir -p "$output/src/std" "$output/lib" "$output/bin" "$output/index"
tests="$root/patches/gerbil-v19-darwin/tests"
cp "$root/.data/d1391-runtime-object-source/src/std/make.ss" "$output/src/std/make.ss"
cp "$root/.data/d1391-runtime-object-source/src/std/gerbil.pkg" "$output/src/std/gerbil.pkg"
cp "$tests/native_capture_probe.ss" "$output/src/probe.ss"
cp "$tests/native_capture_executable_probe.ss" "$output/src/executable-probe.ss"
driver="$runtime/bin"
if test -f "$native/gambuild-C" && test -f "$native/gambit-static-object-reuse"; then
  driver="$native"
fi
cp "$driver/gambuild-C" "$driver/gambit-static-object-reuse" "$native/gambit-file-sha256" "$output/bin/"
ln -s "$native/gsc" "$output/bin/gsc"
ln -s "$interpreter" "$output/bin/gxi"
cd "$output"
git init -q
git apply --check "$root/patches/gerbil-v19-darwin/$patch"
git apply "$root/patches/gerbil-v19-darwin/$patch"
rg -q 'GAMBIT_DARWIN_NATIVE_GENERATED_C' "$output/src/std/make.ss"
export GERBIL_HOME="$runtime" GERBIL_GSC="$output/bin/gsc"
export GERBIL_GCC=/opt/homebrew/bin/gcc-16
export PATH="$output/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export SDKROOT="$(xcrun --sdk macosx --show-sdk-path)"
export LIBRARY_PATH="$(brew --prefix openssl@3)/lib:$(brew --prefix sqlite)/lib:$(brew --prefix zlib)/lib"
export GAMBOPT="~~bin=$output/bin,~~lib=$runtime/lib,~~include=$runtime/include"
unset GAMBIT_DARWIN_NATIVE_GENERATED_C GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS
unset GAMBIT_GENERATED_C_PRODUCER_INDEX GAMBIT_GENERATED_C_BATCH_DIGESTS
cd "$output/src"
export CAPTURE_FIXTURE="$output"
"$output/bin/gxi" -e '(import :gerbil/compiler)
  (compile-module "std/make.ss" [output-dir: (string-append (getenv "CAPTURE_FIXTURE") "/lib")
                                 optimize: #t debug: #t invoke-gsc: #t generate-ssxi: #t])
  (execute-pending-compile-jobs!)' > "$output/prepare.log" 2>&1
rg -q 'GAMBIT_DARWIN_NATIVE_GENERATED_C' "$output/lib/std/make~0.scm"
export GERBIL_LOADPATH="$output/lib"
"$output/bin/gxi" -e '(import :std/make)
  (make ["probe"] srcdir: (current-directory)
        libdir: (string-append (getenv "CAPTURE_FIXTURE") "/control/lib"))' \
  > "$output/control.log" 2>&1
test ! -f "$output/control/lib/probe~0.c.generation-proof"
export GAMBIT_DARWIN_NATIVE_GENERATED_C=1 GAMBIT_GENERATED_C_IN_PROCESS_DIGESTS=1
export GAMBIT_GENERATED_C_BATCH_DIGESTS=1 GAMBIT_GENERATED_C_PRODUCER_INDEX="$output/index"
"$output/bin/gxi" -e '(import :std/make :std/misc/process)
  (let* ((root (getenv "CAPTURE_FIXTURE"))
         (library (string-append root "/candidate/lib"))
         (source (string-append library "/static/probe.scm")))
    (make ["probe"] srcdir: (current-directory) libdir: library)
    (unless (file-exists? (string-append library "/probe~0.c.generation-proof"))
      (error "native producer did not publish proof"))
    (run-process/batch [(getenv "GERBIL_GSC") "-e"
                  (string-append "(load \""
                    (path-expand "../../patches/gerbil-v19-darwin/tests/native_capture_context_probe.scm"
                                 root) "\")")])
    (run-process/batch [ (getenv "GERBIL_GSC") "-link" "-target" "C"
                   "-o" (string-append root "/closure.c") source ]))' \
  > "$output/candidate.log" 2>&1
rg -q '^GAMBIT-NATIVE-PRODUCED-C-LINK-HIT 1$' "$output/candidate.log"
cp "$output/closure.c" "$output/native-closure.c"
"$runtime/bin/gsc" -link -target C -o "$output/closure.c" \
  "$output/candidate/lib/static/probe.scm" > "$output/original-link.log" 2>&1
cmp "$output/closure.c" "$output/native-closure.c"
export GERBIL_LOADPATH="$output/lib:$output/candidate/lib"
"$output/bin/gxi" -e '(import :probe) (unless (= (answer) 17) (error "dynamic ABI regression"))' \
  > "$output/dynamic-load.log" 2>&1
if test "${4:-all-producers}" = planned-producers; then
  mkdir "$output/executable-index"
  export GAMBIT_GENERATED_C_PRODUCER_INDEX="$output/executable-index"
  export GERBIL_LOADPATH="$output/lib:$output/executable/lib:$runtime/lib"
  "$output/bin/gxi" -e '(import :std/make)
    (make ["probe" [exe: "executable-probe" bin: "executable-probe"]]
      srcdir: (current-directory)
      libdir: (string-append (getenv "CAPTURE_FIXTURE") "/executable/lib")
      bindir: (string-append (getenv "CAPTURE_FIXTURE") "/executable/bin"))' \
    > "$output/executable-build.log" 2>&1
  test -z "$(ls -A "$output/executable-index")"
  "$output/executable/bin/executable-probe" > "$output/executable-run.log" 2>&1
  rg -q '^PLANNED-EXECUTABLE-OK$' "$output/executable-run.log"
fi
printf 'STD-MAKE-NATIVE-CAPTURE-OK default-fallback producer-proof link-adoption link-byte-parity dynamic-load\n'
