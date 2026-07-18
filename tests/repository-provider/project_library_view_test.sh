#!/usr/bin/env bash
set -euo pipefail

receipt="$1"
clan_ready="$2"
gslph_ready="$3"
output="$4"

jq -e '
  (.schema == "gerbil-bazel.local-toolchain-receipt.v1" or
   .schema == "gerbil-bazel.prebuilt-toolchain-receipt.v1") and
  .dependencyPolicy == "project-library-view" and
  .dependencyState.clan == "ready" and
  .dependencyState.gslph == "ready" and
  .dependencyState["missing-package"] == "missing"
' "$receipt" >/dev/null

grep -Fx 'clan ready' "$clan_ready" >/dev/null
grep -Fx 'gslph ready' "$gslph_ready" >/dev/null
printf 'project-library-view passed\n' >"$output"
