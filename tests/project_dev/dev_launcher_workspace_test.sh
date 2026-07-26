#!/usr/bin/env bash
set -euo pipefail

launcher="${TEST_SRCDIR}/$1"
workspace="${TEST_SRCDIR}/${TEST_WORKSPACE}"

cd "$TEST_TMPDIR"
BUILD_WORKSPACE_DIRECTORY="$workspace" \
PROJECT_DEV_EXPECTED_WORKSPACE="$workspace" \
  "$launcher" compile
