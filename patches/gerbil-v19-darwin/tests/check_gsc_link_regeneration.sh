#!/usr/bin/env bash
# A copied real module only; never run against the shared dependency prefix.
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
source=${1:?source module .scm required}
output=${2:?fresh .data output required}
case "$output" in "$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
test -f "$source"
test -f "${source%.scm}.c"
mkdir -p "$output"
module=$(basename "${source%.scm}")
cp -p "$source" "$output/$module.scm"
cp -p "${source%.scm}.c" "$output/$module.c"
home="$root/.data/d1391-runtime-object-source/build"
gsc="$home/bin/gsc"
export GERBIL_HOME="$home"
export GAMBOPT="~~bin=$home/bin,~~lib=$home/lib,~~include=$home/include"
unset GERBIL_BUILD_PREFIX
cd "$output"
shasum -a 256 "$gsc" > compiler.sha256
shasum -a 256 "$module.scm" "$module.c" > before.sha256
/usr/bin/stat -f '%Fm %z %N' "$module.c" > before.stat
"$gsc" -link -flat "$module.scm" > scheme-link.log 2>&1
shasum -a 256 "$module.scm" "$module.c" > after-scheme.sha256
/usr/bin/stat -f '%Fm %z %N' "$module.c" > after-scheme.stat
test -f "${module}_.c"
cp "${module}_.c" scheme-link.c
"$gsc" -link -flat "$module.c" > c-link.log 2>&1
shasum -a 256 "$module.scm" "$module.c" > after-c.sha256
/usr/bin/stat -f '%Fm %z %N' "$module.c" > after-c.stat
cmp after-scheme.sha256 after-c.sha256
cmp after-scheme.stat after-c.stat
cmp scheme-link.c "${module}_.c"
"$gsc" -link -flat "$module.scm" > repeated-scheme-link.log 2>&1
shasum -a 256 "$module.scm" "$module.c" > after-repeated-scheme.sha256
/usr/bin/stat -f '%Fm %z %N' "$module.c" > after-repeated-scheme.stat
cmp after-scheme.sha256 after-repeated-scheme.sha256
if cmp -s after-scheme.stat after-repeated-scheme.stat; then
  printf 'DENY: repeated Scheme input did not demonstrate a C rewrite\n' >&2
  exit 1
fi
cmp scheme-link.c "${module}_.c"
cmp "$source" "$module.scm"
if [[ ${3:-} == --object-options ]]; then
  "$gsc" -obj -cc-options '-O0' "$module.c" > object-o0.log 2>&1
  cp "$module.o" object-o0.o
  "$gsc" -obj -cc-options '-O2' "$module.c" > object-o2.log 2>&1
  cmp after-repeated-scheme.sha256 <(shasum -a 256 "$module.scm" "$module.c")
  if cmp -s object-o0.o "$module.o"; then
    printf 'DENY: options probe did not distinguish native objects\n' >&2
    exit 1
  fi
  shasum -a 256 object-o0.o "$module.o" > object-options.sha256
  printf 'OBJECT-OPTIONS-INVALIDATION-REQUIRED\n'
fi
printf 'LINK-REGENERATION-CONTROL-OK\n'
