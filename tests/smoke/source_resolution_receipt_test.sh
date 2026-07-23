#!/usr/bin/env bash
set -euo pipefail

receipt="${TEST_SRCDIR:?}/$1"

grep -Eq '"schema"[[:space:]]*:[[:space:]]*"gerbil-bazel\.dependency-source-resolution-receipt\.v1"' "$receipt"
grep -Eq '"logicalPackage"[[:space:]]*:[[:space:]]*"clan"' "$receipt"
grep -Eq '"resolutionMode"[[:space:]]*:[[:space:]]*"legacy-unique-source"' "$receipt"
grep -Eq '"sourceFileCount"[[:space:]]*:[[:space:]]*1' "$receipt"
grep -Eq '"outcome"[[:space:]]*:[[:space:]]*"resolved"' "$receipt"
