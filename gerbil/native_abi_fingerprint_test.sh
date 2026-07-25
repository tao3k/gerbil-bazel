#!/usr/bin/env bash
set -euo pipefail

fingerprint=${1:?native ABI fingerprint tool is required}
root=${TEST_TMPDIR:-${TMPDIR:-/tmp}}/native-abi-fingerprint-test
first=$root/first
second=$root/second
mkdir -p "$first" "$second"

host_fingerprint=$("$fingerprint")
if [[ ! "$host_fingerprint" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'zero-argument host fingerprint is not a SHA-1 value\n' >&2
  exit 1
fi

printf 'same tool bytes\n' >"$first/tool"
cp "$first/tool" "$second/tool"

first_fingerprint=$("$fingerprint" compiler "$first/tool")
relocated_fingerprint=$("$fingerprint" compiler "$second/tool")
if [[ "$first_fingerprint" != "$relocated_fingerprint" ]]; then
  printf 'fingerprint changed after path-only relocation\n' >&2
  exit 1
fi

printf 'different tool bytes\n' >"$second/tool"
changed_content_fingerprint=$("$fingerprint" compiler "$second/tool")
if [[ "$first_fingerprint" == "$changed_content_fingerprint" ]]; then
  printf 'fingerprint did not change after tool content changed\n' >&2
  exit 1
fi

changed_role_fingerprint=$("$fingerprint" linker "$first/tool")
if [[ "$first_fingerprint" == "$changed_role_fingerprint" ]]; then
  printf 'fingerprint did not change after tool role changed\n' >&2
  exit 1
fi
