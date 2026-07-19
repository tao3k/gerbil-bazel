#!/usr/bin/env bash
set -euo pipefail

receipt="$1"
clan_ready="$2"
gslph_ready="$3"
output="$4"

grep -Eq '"schema"[[:space:]]*:[[:space:]]*"gerbil-bazel\.(local|prebuilt)-toolchain-receipt\.v1"' "$receipt"
grep -Eq '"dependencyPolicy"[[:space:]]*:[[:space:]]*"project-library-view"' "$receipt"
grep -Eq '"clan"[[:space:]]*:[[:space:]]*"ready"' "$receipt"
grep -Eq '"gslph"[[:space:]]*:[[:space:]]*"ready"' "$receipt"
grep -Eq '"missing-package"[[:space:]]*:[[:space:]]*"missing"' "$receipt"

grep -Fx 'clan ready' "$clan_ready" >/dev/null
grep -Fx 'gslph ready' "$gslph_ready" >/dev/null
printf 'project-library-view passed\n' >"$output"
