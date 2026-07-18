#!/usr/bin/env bash
set -euo pipefail

receipt="${TEST_SRCDIR:?}/$1"

grep -F '"schema": "gerbil-bazel.local-toolchain-receipt.v1"' "$receipt" >/dev/null
grep -F '"dependencyPolicy": "project-library-view"' "$receipt" >/dev/null
grep -F '"clan": "ready"' "$receipt" >/dev/null
grep -F '"gslph": "ready"' "$receipt" >/dev/null
