#!/usr/bin/env bash
set -euo pipefail

resolve_runfile() {
  local logical_path=${1:?runfile key is required}
  local candidate

  if [[ "$logical_path" = /* && -e "$logical_path" ]]; then
    printf '%s\n' "$logical_path"
    return
  fi
  if [[ -n "${RUNFILES_DIR:-}" && -e "$RUNFILES_DIR/$logical_path" ]]; then
    printf '%s\n' "$RUNFILES_DIR/$logical_path"
    return
  fi
  if [[ -n "${TEST_SRCDIR:-}" && -e "$TEST_SRCDIR/$logical_path" ]]; then
    printf '%s\n' "$TEST_SRCDIR/$logical_path"
    return
  fi
  if [[ -n "${RUNFILES_MANIFEST_FILE:-}" ]]; then
    candidate=$(
      awk -v key="$logical_path" '$1 == key {sub($1 " ", ""); print; exit}' \
        "$RUNFILES_MANIFEST_FILE"
    )
    if [[ -n "$candidate" && -e "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return
    fi
  fi
  printf 'runfile not found: %s\n' "$logical_path" >&2
  return 1
}

graph_receipt=$(resolve_runfile "${1:?package graph receipt is required}")
build_receipt=$(resolve_runfile "${2:?package build receipt is required}")

jq -e '
  .schema == "gerbil-bazel.package-graph.v1" and
  .rootPackage == "example.invalid/graph-root" and
  (.packages | length == 1) and
  .packages[0].reference == "//root" and
  .packages[0].revision == "" and
  .packages[0].target == "//:package_0" and
  .packages[0].acquisition == {"kind": "workspace"} and
  .packages[0].manifest.schema == "gerbil-bazel.package-manifest.v1" and
  .packages[0].manifest.package == "example.invalid/graph-root" and
  (.packages[0].manifest | has("build") | not) and
  (.packages[0].manifest.sources | any(.path == "build.ss")) and
  (.packages[0].manifest.sources | any(.path == "gerbil.pkg"))
' "$graph_receipt" >/dev/null

jq -e '
  .schema == "gerbil-bazel.package-receipt.v1" and
  .status == "ok" and
  .packageIdentity == "example.invalid/graph-root" and
  .packageReference == "example.invalid/graph-root" and
  .packageRevision == ""
' "$build_receipt" >/dev/null

echo "Gerbil package graph repository: ok"
