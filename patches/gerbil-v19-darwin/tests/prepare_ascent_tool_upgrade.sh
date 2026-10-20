#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
original=${1:?frozen owned ASCENT workspace required}
output=${2:?fresh owned COW workspace required}
case "$original:$output" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test ! -e "$output"
test "$(git -C "$original/project" rev-parse HEAD)" = 21e3638687d42ecfc36acebb28991987435ebc60
test -z "$(git -C "$original/project" status --porcelain --untracked-files=no)"
mkdir "$output"
for name in project toolchain dependencies; do
  /bin/cp -cR "$original/$name" "$output/$name"
done
for name in toolchain-dynamic-references.json dependency-dynamic-references.json; do
  cp "$original/$name" "$output/$name"
done
bin="$output/toolchain/bin"
test ! -L "$bin" && test ! -L "$bin/gambuild-C"
test -L "$bin/gcc" && test "$(readlink "$bin/gcc")" = /opt/homebrew/bin/gcc-16
cp /opt/homebrew/bin/gcc-16 "$bin/compiler"
chmod u+w "$bin/compiler"
cmp /opt/homebrew/bin/gcc-16 "$bin/compiler"
# Preserve GCC's configured relative runtime/program layout without copying it.
cc1=$(/opt/homebrew/bin/gcc-16 -print-prog-name=cc1)
emutls=$(/opt/homebrew/bin/gcc-16 -print-file-name=libemutls_w.a)
test -f "$cc1" && test -f "$emutls"
program_root=$(cd "$(dirname "$cc1")/../.." && pwd)
library_root=$(cd "$(dirname "$emutls")/../.." && pwd)
mkdir -p "$output/toolchain/libexec" "$output/toolchain/lib/gcc/current"
test ! -e "$output/toolchain/libexec/gcc"
test ! -e "$output/toolchain/lib/gcc/current/gcc"
ln -s "$program_root" "$output/toolchain/libexec/gcc"
ln -s "$library_root" "$output/toolchain/lib/gcc/current/gcc"
sed "s|/opt/homebrew/bin/gcc-16|$bin/compiler|g" "$bin/gambuild-C" > "$bin/gambuild-C.pending"
chmod +x "$bin/gambuild-C.pending"
mv "$bin/gambuild-C.pending" "$bin/gambuild-C"
rm "$bin/gcc"
ln -s "$bin/compiler" "$bin/gcc"
unset GCC_EXEC_PREFIX COMPILER_PATH
test -f "$("$bin/compiler" -print-prog-name=cc1)"
test -f "$("$bin/compiler" -print-file-name=libemutls_w.a)"
printf 'int main(void) { return 0; }\n' | "$bin/compiler" -x c - -lemutls_w -o "$output/relocation-probe"
"$output/relocation-probe"
printf 'ASCENT-TOOL-UPGRADE-ISOLATION-READY COW private-GNU-GCC\n'
