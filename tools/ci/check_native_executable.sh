#!/usr/bin/env bash
# Exercise actual standard Make, native objects, linker and resulting executable.
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
work=$(mktemp -d "${TMPDIR:-/tmp}/gerbil-executable-closure.XXXXXX")
trap 'status=$?; if [ "$status" -eq 0 ]; then rm -rf "$work"; else mkdir -p "$root/.ci/receipts"; cp -Rp "$work" "$root/.ci/receipts/"; fi' EXIT
deadline=$(command -v timeout || command -v gtimeout)
for variant in positive object-failure; do
  directory="$work/$variant"
  mkdir -p "$directory"
  cp "$root/t/executable-closure-test.ss" "$directory/main.ss"
  printf '%s\n' '(package: native-executable-contract)' > "$directory/gerbil.pkg"
  if [ "$variant" = positive ]; then
    spec='((exe: "main" bin: "closure-main"))'
  else
    # This valid native compiler request must fail during object compilation.
    spec='((exe: "main" bin: "closure-main" "-cc-options" "-fnative-executable-negative-control"))'
  fi
  printf '%s\n' '#!/usr/bin/env gxi' '(import :std/build-script)' "(defbuild-script '$spec)" > "$directory/build.ss"
  chmod +x "$directory/build.ss"
  status=0
  (cd "$directory" && env GERBIL_PATH="$directory/.gerbil" GERBIL_BUILD_VERBOSE=3 GAMBOPT=max-heap=2G,debug=q \
    "$deadline" --signal=TERM --kill-after=5s 180s gerbil -:max-heap=2G,debug=q build) \
    > "$directory/build.log" 2>&1 || status=$?
  if [ "$variant" = positive ]; then
    test "$status" -eq 0
    grep -F 'compile-executable-object' "$directory/build.log" >/dev/null
    result=$("$deadline" --signal=TERM --kill-after=5s 180s "$directory/.gerbil/bin/closure-main" -:max-heap=2G)
    test "$result" = 42
  else
    test "$status" -ne 0
    test "$status" -ne 124
    grep -F 'native-executable-negative-control' "$directory/build.log" >/dev/null
    test ! -e "$directory/.gerbil/bin/closure-main"
  fi
done
printf 'NATIVE-EXECUTABLE-CLOSURE-OK\n'
