#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../../.." && pwd)
cache=${1:?owned native cache required}
receipt=${2:?existing owned receipt required}
expected=${3:?expected trace inventory size required}
[[ "$expected" =~ ^[1-9][0-9]*$ ]] || exit 2
case "$cache:$receipt" in "$root"/.data/*:"$root"/.data/*) ;; *) exit 2 ;; esac
test -d "$cache" && test ! -L "$cache"
test -d "$receipt" && test ! -L "$receipt"
test ! -e "$receipt/traces"
mkdir "$receipt/traces"
count=0
while IFS= read -r file; do
  test -f "$file" && test ! -L "$file"
  target="$receipt/traces/${file##*/}"
  test ! -e "$target" && test ! -L "$target"
  mv "$file" "$target"
  count=$((count+1))
done < <(rg --files --hidden --no-ignore "$cache" -g '*.gambit-static-key-trace')
test "$count" = "$expected"
printf 'STATIC-KEY-TRACES-COLLECTED %s\n' "$count"
