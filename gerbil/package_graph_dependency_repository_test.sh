#!/usr/bin/env bash
set -euo pipefail

receipt=${1:?package graph receipt is required}
if [[ "$receipt" != /* ]]; then
  receipt="${TEST_SRCDIR:?TEST_SRCDIR is required}/$receipt"
fi
build_receipt=${2:?package build receipt is required}
if [[ "$build_receipt" != /* ]]; then
  build_receipt="${TEST_SRCDIR:?TEST_SRCDIR is required}/$build_receipt"
fi
gxpkg_manifest=${3:?gxpkg manifest is required}
if [[ "$gxpkg_manifest" != /* ]]; then
  gxpkg_manifest="${TEST_SRCDIR:?TEST_SRCDIR is required}/$gxpkg_manifest"
fi

jq -e '
  .schema == "gerbil-bazel.package-graph.v1" and
  .rootPackage == "example.invalid/graph-with-dependency" and
  (.packages | length == 2) and
  (.packages | any(
    .reference == "github.com/mighty-gerbils/gerbil-utils" and
    .revision == "f45a4ef3bfecd2af39e114ed736ce9082cbb8244" and
    .manifest.package == "clan" and
    .acquisition.kind == "archive" and
    .acquisition.sha256 == "e7777c505e71de490dc05f8e3ff4473dddbc998a99899c085d31750add551296"
  )) and
  (.packages | any(
    .reference == "//root" and
    .manifest.package == "example.invalid/graph-with-dependency" and
    .acquisition.kind == "workspace"
  ))
' "$receipt" >/dev/null

jq -e '
  .schema == "gerbil-bazel.package-receipt.v1" and
  .status == "ok" and
  .packageIdentity == "example.invalid/graph-with-dependency" and
  .packageReference == "example.invalid/graph-with-dependency" and
  .packageRevision == ""
' "$build_receipt" >/dev/null

grep -F '("example.invalid/graph-with-dependency" . "unknown")' \
  "$gxpkg_manifest" >/dev/null
if grep -F '(def version-manifest' "$gxpkg_manifest" >/dev/null; then
  echo "gxpkg dependency manifest must be a plain datum" >&2
  exit 1
fi

echo "Gerbil package dependency graph repository: ok"
