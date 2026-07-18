#!/usr/bin/env bash
set -euo pipefail

receipt="$1"
expected_state="$2"
output="$3"

grep -Eq '"schema"[[:space:]]*:[[:space:]]*"gerbil-bazel\.(local|prebuilt)-toolchain-receipt\.v1"' "$receipt"
grep -Eq '"dependencyPolicy"[[:space:]]*:[[:space:]]*"project-library-view"' "$receipt"
grep -Eq "\"clan\"[[:space:]]*:[[:space:]]*\"$expected_state\"" "$receipt"
grep -Eq "\"gslph\"[[:space:]]*:[[:space:]]*\"$expected_state\"" "$receipt"
grep -Eq '"missing-package"[[:space:]]*:[[:space:]]*"missing"' "$receipt"

printf 'project dependency state %s\n' "$expected_state" >"$output"
