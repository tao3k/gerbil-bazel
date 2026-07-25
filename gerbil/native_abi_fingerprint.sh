#!/usr/bin/env bash
set -euo pipefail

hash_stream() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 1 | awk '{print $1}'
  elif command -v sha1sum >/dev/null 2>&1; then
    sha1sum | awk '{print $1}'
  else
    printf 'Gerbil Bazel requires shasum or sha1sum for ABI discovery\n' >&2
    exit 1
  fi
}

if (( $# % 2 != 0 )); then
  printf 'usage: %s ROLE TOOL [ROLE TOOL ...]\n' "$0" >&2
  exit 2
fi

{
  uname -srm
  while (( $# != 0 )); do
    role=$1
    tool=$2
    shift 2
    printf '%s\n' "$role"
    if command -v shasum >/dev/null 2>&1; then
      shasum -a 1 "$tool" | awk '{print $1}'
    else
      sha1sum "$tool" | awk '{print $1}'
    fi
  done
} | hash_stream
