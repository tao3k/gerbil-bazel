#!/usr/bin/env bash
set -euo pipefail
if test -n "${GAMBIT_GENERATION_TRACE:-}"; then
  case "${1:-}" in -*) operation=$1 ;; *) operation=file-or-eval ;; esac
  printf '%s %s\n' "$$" "$operation" >> "$GAMBIT_GENERATION_TRACE"
fi
bin=$(cd "$(dirname "$0")" && pwd)
original="$bin/gsc-original"
if test "${GAMBIT_DARWIN_GENERATED_C_REUSE:-}" != 1 || test "$(uname -s)" != Darwin; then
  exec "$original" "$@"
fi
# Only the already-qualified runtime producer shape is intercepted.
parse_request() {
  test "${1:-}" = -c || return 1
  shift
  output= input= alias= linker= target=
  while test "$#" -gt 0; do
    case "$1" in
      -o) test "$#" -ge 2 && test -z "$output" || return 1; output=$2; shift 2 ;;
      -module-ref) test "$#" -ge 2 && test -z "$alias" || return 1; alias=$2; shift 2 ;;
      -linker-name) test "$#" -ge 2 && test -z "$linker" || return 1; linker=$2; shift 2 ;;
      -target) test "$#" -ge 2 && test -z "$target" && test "$2" = C || return 1; target=$2; shift 2 ;;
      -*) return 1 ;;
      *) test "$#" = 1 && test -z "$input" || return 1; input=$1; shift ;;
    esac
  done
  test -n "$alias" && test "$alias" = "$linker" || return 1
  case "$input:$output" in *.scm:*.c) ;; *) return 1 ;; esac
  test "$(basename "${input%.scm}")" = "$(basename "${output%.c}")" || return 1
  test -f "$input" && test ! -L "$input" && test -d "$(dirname "$output")"
}
if ! parse_request "$@"; then exec "$original" "$@"; fi
request=$(mktemp "$(dirname "$output")/.gambit-generation-request.XXXXXX")
work=
cleanup() { rm -f -- "$request"; if test -n "$work"; then rm -rf -- "$work"; fi; }
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
work=$(mktemp -d "$(dirname "$output")/.gambit-generation-work.XXXXXX")
printf '%s\0' "$bin" "$input" "$output" "$alias" "$target" "$work" > "$request"
GAMBIT_GENERATION_REQUEST="$request" GAMBIT_GENERATION_ADAPTER_BIN="$bin" "$original" \
  -e '(load (string-append (getenv "GAMBIT_GENERATION_ADAPTER_BIN") "/gambit-generated-c-reads.scm"))' \
  -e '(load (string-append (getenv "GAMBIT_GENERATION_ADAPTER_BIN") "/gambit-generated-c-closure.scm"))' \
  -e '(load (string-append (getenv "GAMBIT_GENERATION_ADAPTER_BIN") "/gambit-generated-c-adapter.scm"))' \
  -e '(with-exception-catcher (lambda (failure) (display-exception failure (current-error-port)) (exit 70)) (lambda () (run-generated-c-request!)))'
