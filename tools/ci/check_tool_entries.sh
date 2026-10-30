#!/usr/bin/env bash
# Exercise the published CLI tools; Suite files only declare tests.
set -euo pipefail
mkdir -p .ci/receipts
work=$(mktemp -d "${TMPDIR:-/tmp}/gerbil-tool-entry.XXXXXX")
trap 'status=$?; if [ "$status" -eq 0 ]; then rm -rf "$work"; else cp -Rp "$work" .ci/receipts/; printf "TOOL-ENTRY-FAILURE %s\n" "$work" >&2; fi' EXIT
cat > "$work/tagged.ss" <<'SCM'
(export answer)
(def answer 42)
SCM
cat > "$work/passing-test.ss" <<'SCM'
(import :std/test)
(export passing-test)
(def passing-test (test-suite "native entry" (test-case "answer" (check 42 => 42))))
SCM
cat > "$work/failing-test.ss" <<'SCM'
(import :std/test)
(export failing-test)
(def failing-test (test-suite "native entry" (test-case "failure" (check #f => #t))))
SCM
# Each command gets a fresh process. No alternate module launcher or tag format.
gxtags -o "$work/TAGS" "$work/tagged.ss"
test -s "$work/TAGS"
grep -F answer "$work/TAGS" >/dev/null
gerbil tags -o "$work/unified.TAGS" "$work/tagged.ss"
test -s "$work/unified.TAGS"
grep -F answer "$work/unified.TAGS" >/dev/null
gxtest -v 3 "$work/passing-test.ss"
gerbil test -v 3 "$work/passing-test.ss"
for tool in gxtest gerbil; do
  status=0
  if [ "$tool" = gerbil ]; then
    gerbil test -v 3 "$work/failing-test.ss" > "$work/$tool.log" 2>&1 || status=$?
  else
    gxtest -v 3 "$work/failing-test.ss" > "$work/$tool.log" 2>&1 || status=$?
  fi
  cat "$work/$tool.log"
  test "$status" -eq 42
  if [ "$tool" = gerbil ]; then
    gerbil test -h > "$work/$tool-help.log" 2>&1
    status=0
    gerbil test "$work/missing-test.ss" > "$work/$tool-missing.log" 2>&1 || status=$?
  else
    gxtest -h > "$work/$tool-help.log" 2>&1
    status=0
    gxtest "$work/missing-test.ss" > "$work/$tool-missing.log" 2>&1 || status=$?
  fi
  test "$status" -ne 0
done
printf 'GERBIL-TOOL-ENTRIES-OK\n'
