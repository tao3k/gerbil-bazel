#!/usr/bin/env bash
set -euo pipefail

resolve_runfile() {
  local key=$1
  local runfiles_dir=${RUNFILES_DIR:-${BASH_SOURCE[0]}.runfiles}
  local runfiles_manifest=${RUNFILES_MANIFEST_FILE:-${BASH_SOURCE[0]}.runfiles_manifest}
  local manifest_key
  local manifest_path
  if [[ -e "$key" ]]; then
    printf '%s\n' "$key"
    return 0
  fi
  if [[ -e "$runfiles_dir/$key" ]]; then
    printf '%s\n' "$runfiles_dir/$key"
    return 0
  fi
  if [[ -f "$runfiles_manifest" ]]; then
    while IFS=' ' read -r manifest_key manifest_path; do
      if [[ "$manifest_key" == "$key" ]]; then
        printf '%s\n' "$manifest_path"
        return 0
      fi
    done < "$runfiles_manifest"
  fi
  printf 'cannot resolve AOT runfile: %s\n' "$key" >&2
  return 1
}

plan=$(resolve_runfile "$1")
receipt=$(resolve_runfile "$2")
gxi=$(resolve_runfile "$3")
validator=$(resolve_runfile "$4")
plan_schema=$(resolve_runfile "$5")
receipt_schema=$(resolve_runfile "$6")

test -s "$plan"
test -s "$receipt"

grep -Fq '"schema": "gerbil-bazel.native-link-plan.v1"' "$plan"
grep -Fq '"linkLibraries": [' "$plan"
grep -Fq '"static=gambit"' "$plan"
grep -Fq '"schema": "gerbil-bazel.aot-receipt.v1"' "$receipt"
grep -Fq '"module": "example.invalid/test-package/src/value"' "$receipt"
grep -Fq '"nativeAbiFingerprint":' "$receipt"

"$gxi" "$validator" "$plan_schema" "$receipt_schema" "$plan" "$receipt"

if grep -Fq '/Users/' "$plan" || grep -Fq '/home/' "$plan"; then
  printf 'AOT link plan contains a host-absolute path\n' >&2
  exit 1
fi

printf 'gerbil-aot-object-plan-ok\n'
