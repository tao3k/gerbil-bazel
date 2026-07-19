#!/usr/bin/env bash
set -euo pipefail

{{ENVIRONMENT}}

exec {{GSC}} -cc "$GERBIL_GCC" "$@"
