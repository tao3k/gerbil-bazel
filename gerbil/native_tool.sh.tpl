#!/usr/bin/env bash
set -euo pipefail

{{ENVIRONMENT}}
export GERBIL_NATIVE_ABI={{NATIVE_ABI}}
exec {{TOOL}} "$@"
